/******************************************************************************
 * File        : RobotAPI.cpp
 *
 * Description :
 *      Robot Hardware Abstraction API Implementation.
 *      Supports ESP32 PWM motor control using GPIO pin definitions.
 ******************************************************************************/

#include "RobotAPI.h"
#include "MotionConfig.h"
#include <Arduino.h>
#include <esp32-hal-ledc.h>

// Sửa đường dẫn: từ Services/Robot lên src, rồi vào Devices
#include "../../Devices/Touch.h"
#include "../../Devices/LineSensor.h"
#include "../../Devices/LightSensor.h"
#include "../../Devices/ColorSensor.h"
#include "../../Devices/SensorConfig.h"
#include "../../HardwareAbstraction/GPIO.h"
#include "../../Sensor/SensorManager.h"
#include "../../Sensor/TCRT5000.h"
#include "../../Sensor/SensorID.h"
#include "../../Sensor/Ultrasonic.h"
#include "../../Sensor/IMUSensor.h"

// Line Follower
#include "../../Services/Line/LineFollower.h"

// Heading Estimator & Controller
#include "../../Services/Motion/HeadingEstimator.h"
#include "../../Services/Motion/HeadingController.h"

// VM (for diagnostics)
#include "../../Services/VM/VM.h"

// Khai báo HeadingEstimator toàn cục (được định nghĩa trong main.ino)
extern HeadingEstimator g_headingEstimator;
extern bool g_robotReady;
extern VM vm;

namespace RobotAPI {

// Cấu hình PWM cho ESP32
#define PWM_FREQ 5000
#define PWM_RES 8 // 0-255

// Kênh PWM: dùng 4 kênh cho 4 chân điều khiển
static const int PWM_CH_L_IN1 = 0;
static const int PWM_CH_L_IN2 = 1;
static const int PWM_CH_R_IN3 = 2;
static const int PWM_CH_R_IN4 = 3;

// Định nghĩa các đối tượng cảm biến (toàn cục trong namespace)
static Touch touch0(ROBOT_PIN_5);
static Touch touch1(ROBOT_PIN_5);
static LightSensor lightSensor(ROBOT_PIN_5);
static ColorSensor colorSensor;

// ---- STOP Reason Diagnostics ----
enum StopReason {
    STOP_REASON_UNKNOWN = 0,
    STOP_REASON_COMMAND_STOP,
    STOP_REASON_VM_STOP,
    STOP_REASON_HEADING_SAFETY,
    STOP_REASON_MOTOR_SAFETY,
    STOP_REASON_IMU_FAILURE,
    STOP_REASON_CONTROLLER_ERROR,
    STOP_REASON_WATCHDOG,
    STOP_REASON_PROGRAM_END,
};

static const char* stopReasonToString(StopReason reason) {
    switch (reason) {
        case STOP_REASON_COMMAND_STOP:   return "COMMAND_STOP";
        case STOP_REASON_VM_STOP:        return "VM_STOP";
        case STOP_REASON_HEADING_SAFETY: return "HEADING_SAFETY";
        case STOP_REASON_MOTOR_SAFETY:   return "MOTOR_SAFETY";
        case STOP_REASON_IMU_FAILURE:    return "IMU_FAILURE";
        case STOP_REASON_CONTROLLER_ERROR: return "CONTROLLER_ERROR";
        case STOP_REASON_WATCHDOG:       return "WATCHDOG";
        case STOP_REASON_PROGRAM_END:    return "PROGRAM_END";
        default:                         return "UNKNOWN";
    }
}

// ---- Forward declarations ----
static void _stopMotion(StopReason reason = STOP_REASON_COMMAND_STOP);
static void _applyMotion();

// ---- Motor control internal ----

static void _setMotorsRaw(int leftSpeed, int rightSpeed) {
    leftSpeed = constrain(leftSpeed, -100, 100);
    rightSpeed = constrain(rightSpeed, -100, 100);

    int leftPWM = abs(leftSpeed) * g_motionConfig.pwmPerSpeed;
    int rightPWM = abs(rightSpeed) * g_motionConfig.pwmPerSpeed;
    leftPWM = constrain(leftPWM, 0, 255);
    rightPWM = constrain(rightPWM, 0, 255);

    if (leftSpeed >= 0) {
        ledcWrite(MOTOR_L_IN1_PIN, leftPWM);
        ledcWrite(MOTOR_L_IN2_PIN, 0);
    } else {
        ledcWrite(MOTOR_L_IN1_PIN, 0);
        ledcWrite(MOTOR_L_IN2_PIN, leftPWM);
    }

    if (rightSpeed >= 0) {
        ledcWrite(MOTOR_R_IN3_PIN, rightPWM);
        ledcWrite(MOTOR_R_IN4_PIN, 0);
    } else {
        ledcWrite(MOTOR_R_IN3_PIN, 0);
        ledcWrite(MOTOR_R_IN4_PIN, rightPWM);
    }
}

static void _setMotors(int leftSpeed, int rightSpeed) {
    leftSpeed = (int)(leftSpeed * g_motionConfig.speedScale * g_motionConfig.leftMotorScale);
    rightSpeed = (int)(rightSpeed * g_motionConfig.speedScale * g_motionConfig.rightMotorScale);
    _setMotorsRaw(leftSpeed, rightSpeed);
}

// ---- Heading Hold Controller ----
static HeadingController g_headingController;
static bool g_headingHoldEnabled = true;
static bool g_isMoving = false;
static int g_currentBaseSpeed = 0;
static int g_currentDirection = 0;
static int g_effectiveLeft = 0;
static int g_effectiveRight = 0;

// ---- Ultrasonic Diagnostic Counters ----
static uint32_t ultraReadCount = 0;
static uint32_t ultraFailCount = 0;

// ---- Stop Motion (with reason) ----
static void _stopMotion(StopReason reason) {
    if (g_isMoving) {
        Serial.printf("[STOP] reason=%s\n", stopReasonToString(reason));
        Serial.printf("[STOP] heading=%.2f target=%.2f error=%.2f correction=%.2f\n",
                      g_headingEstimator.getHeadingDeg(),
                      g_headingController.getTargetHeading(),
                      g_headingController.getLastError(),
                      g_headingController.getLastCorrection());
        Serial.printf("[STOP] effectiveL=%d effectiveR=%d base=%d direction=%d\n",
                      g_effectiveLeft, g_effectiveRight, g_currentBaseSpeed, g_currentDirection);
        Serial.printf("[STOP] vmState=%s\n", vm.IsRunning() ? "RUNNING" : "STOPPED");
    }
    g_isMoving = false;
    g_headingController.stop();
    _setMotorsRaw(0, 0);
    g_effectiveLeft = 0;
    g_effectiveRight = 0;
}

// ---- Apply Motion ----
static void _applyMotion() {
    if (!g_isMoving) {
        _setMotorsRaw(0, 0);
        g_effectiveLeft = 0;
        g_effectiveRight = 0;
        return;
    }

    int baseSpeed = g_currentBaseSpeed;
    int direction = g_currentDirection;
    float correction = 0.0f;

    int baseLeft = (int)(baseSpeed * g_motionConfig.speedScale * g_motionConfig.leftMotorScale);
    int baseRight = (int)(baseSpeed * g_motionConfig.speedScale * g_motionConfig.rightMotorScale);

    if (g_headingHoldEnabled && g_headingController.isActive()) {
        auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
        if (imu && imu->isReady() && imu->isCalibrated()) {
            float currentHeading = g_headingEstimator.getHeadingDeg();
            uint32_t now = millis();
            correction = g_headingController.update(currentHeading, now);

            float error = g_headingController.getLastError();
            if (fabs(error) > 45.0f) {
                Serial.printf("[SAFETY] Heading error exceeded 45 degrees (error=%.2f), stopping robot\n", error);
                _stopMotion(STOP_REASON_HEADING_SAFETY);
                return;
            }
        } else {
            Serial.println("[SAFETY] IMU became invalid during motion, stopping robot");
            _stopMotion(STOP_REASON_IMU_FAILURE);
            return;
        }
    }

    int leftEff, rightEff;
    if (direction < 0) {
        leftEff = -baseLeft - (int)correction;
        rightEff = -baseRight + (int)correction;
    } else {
        leftEff = baseLeft - (int)correction;
        rightEff = baseRight + (int)correction;
    }

    leftEff = constrain(leftEff, -100, 100);
    rightEff = constrain(rightEff, -100, 100);

    g_effectiveLeft = leftEff;
    g_effectiveRight = rightEff;

    _setMotorsRaw(leftEff, rightEff);

    if (g_isMoving && g_headingController.isActive()) {
        static uint32_t lastHeadingDiag = 0;
        uint32_t now = millis();
        if (now - lastHeadingDiag >= 200) {
            lastHeadingDiag = now;
            float target = g_headingController.getTargetHeading();
            float current = g_headingEstimator.getHeadingDeg();
            float error = g_headingController.getLastError();
            float corr = g_headingController.getLastCorrection();
            Serial.printf("[HEADING] Target=%.2f Current=%.2f Error=%.2f Correction=%.2f\n",
                          target, current, error, corr);
            Serial.printf("[MOTOR] EffectiveL=%d EffectiveR=%d Base=%d Direction=%d\n",
                          g_effectiveLeft, g_effectiveRight, g_currentBaseSpeed, g_currentDirection);
        }
    }
}

// ---- Khởi tạo heading controller ----
static void _initHeadingController() {
    g_headingController.init(1.2f, 0.0f, 0.1f, 20.0f);
    g_headingHoldEnabled = true;
    Serial.println("[RobotAPI] Heading controller initialized");
}

// ---- Reset heading controller (exposed for calibration) ----
void resetHeadingController() {
    g_headingController.reset();
    g_headingController.stop();
    g_isMoving = false;
    g_currentBaseSpeed = 0;
    g_currentDirection = 0;
    g_effectiveLeft = 0;
    g_effectiveRight = 0;
    _setMotorsRaw(0, 0);
    Serial.println("[RobotAPI] Heading controller reset");
}

// ---- Bắt đầu di chuyển ----
static void _startMotion(int speed, int direction) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Motion blocked: Robot not ready (calibrating IMU)");
        return;
    }

    if (speed < 0) {
        direction = -direction;
        speed = -speed;
    }
    if (speed > 100) speed = 100;
    if (speed < 0) speed = 0;

    bool newSession = !g_isMoving;

    g_currentBaseSpeed = speed;
    g_currentDirection = direction;
    g_isMoving = true;

    if (newSession) {
        g_headingController.reset();

        if (g_headingHoldEnabled) {
            auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
            if (imu && imu->isReady() && imu->isCalibrated()) {
                float currentHeading = g_headingEstimator.getHeadingDeg();
                g_headingController.start(currentHeading);
                Serial.printf("[Heading] HOLD START target=%.2f deg\n", currentHeading);
            } else {
                g_headingController.stop();
                Serial.println("[Heading] Heading hold unavailable (IMU not calibrated)");
            }
        } else {
            g_headingController.stop();
        }
    } else {
        if (g_headingHoldEnabled && !g_headingController.isActive()) {
            auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
            if (imu && imu->isReady() && imu->isCalibrated()) {
                g_headingController.start(g_headingController.getTargetHeading());
                Serial.printf("[Heading] CONTROLLER RESTART (target=%.2f deg)\n",
                              g_headingController.getTargetHeading());
            }
        }
    }

    _applyMotion();
}

// ===== Public API =====

void setMotorsDirect(int left, int right) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Motion blocked: Robot not ready");
        return;
    }
    _setMotors(left, right);
}

void SetMotorSpeed(int left, int right) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Motion blocked: Robot not ready");
        return;
    }
    _setMotors(left, right);
}

void Forward(int16_t speed) {
    _startMotion(speed, 1);
}

void Backward(int16_t speed) {
    _startMotion(speed, -1);
}

void TurnLeft(int16_t speed) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Motion blocked: Robot not ready");
        return;
    }
    _stopMotion(STOP_REASON_COMMAND_STOP);
    int left = -speed;
    int right = speed;
    _setMotors(left, right);
}

void TurnRight(int16_t speed) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Motion blocked: Robot not ready");
        return;
    }
    _stopMotion(STOP_REASON_COMMAND_STOP);
    int left = speed;
    int right = -speed;
    _setMotors(left, right);
}

void Stop() {
    _stopMotion(STOP_REASON_COMMAND_STOP);
}

void updateMotion() {
    if (g_isMoving && g_robotReady) {
        _applyMotion();
    }
}

bool isRobotReady() {
    return g_robotReady;
}

bool isHeadingHoldActive() {
    return g_headingController.isActive();
}

bool isHeadingHoldEnabled() {
    return g_headingHoldEnabled;
}

void setHeadingHoldEnabled(bool enabled) {
    g_headingHoldEnabled = enabled;
    if (!enabled) {
        g_headingController.stop();
    }
}

void setHeadingHoldGains(float kp, float ki, float kd, float maxCorrection) {
    g_headingController.init(kp, ki, kd, maxCorrection);
}

float getHeadingTarget() { return g_headingController.getTargetHeading(); }
float getHeadingError() { return g_headingController.getLastError(); }
float getHeadingCorrection() { return g_headingController.getLastCorrection(); }
float getHeadingKp() { return g_headingController.getKp(); }
float getHeadingKi() { return g_headingController.getKi(); }
float getHeadingKd() { return g_headingController.getKd(); }
float getHeadingMaxCorrection() { return g_headingController.getMaxCorrection(); }

int getEffectiveLeft() { return g_effectiveLeft; }
int getEffectiveRight() { return g_effectiveRight; }
int getCurrentBaseSpeed() { return g_currentBaseSpeed; }
int getCurrentDirection() { return g_currentDirection; }

// ===== ULTRASONIC DIAGNOSTIC GETTERS =====
uint32_t getUltraReadCount() {
    return ultraReadCount;
}

uint32_t getUltraFailCount() {
    return ultraFailCount;
}

// ===== Sensor API =====

int16_t ReadTouch(int port) {
    bool state = false;
    if (port == 0) state = touch0.read();
    else if (port == 1) state = touch1.read();
    Serial.printf("[%lu] ReadTouch port %d: %d\n", millis(), port, state);
    return state ? 1 : 0;
}

int16_t ReadLight(int channel) {
    int raw = lightSensor.readRaw();
    int corrected = (int)(raw * g_sensorConfig.lightGain + g_sensorConfig.lightOffset);
    Serial.printf("[%lu] ReadLight ch %d: %d\n", millis(), channel, corrected);
    return corrected;
}

int16_t ReadColor() {
    int val = colorSensor.readColor();
    Serial.printf("[%lu] ReadColor: %d\n", millis(), val);
    return val;
}

int16_t ReadLine(int channel) {
    SensorID id;
    switch (channel) {
        case 0: id = SensorID::LineLeft; break;
        case 1: id = SensorID::LineCenter; break;
        case 2: id = SensorID::LineRight; break;
        default: return 0;
    }
    auto sensor = SensorManager::instance().getSensor(id);
    if (sensor) {
        auto lineSensor = static_cast<TCRT5000*>(sensor);
        lineSensor->update();
        return lineSensor->isLineDetected() ? 1 : 0;
    }
    return 0;
}

// ================================================================
// === ULTRASONIC DIAGNOSTIC (ReadUltrasonic) ===
// ================================================================
int16_t ReadUltrasonic() {
    ultraReadCount++;
    auto sensor = SensorManager::instance().getSensor(SensorID::Ultrasonic);
    if (sensor) {
        auto us = static_cast<Ultrasonic*>(sensor);
        us->update();
        float dist = us->distanceCm();
        
        if (dist < 0) {
            ultraFailCount++;
            if (ultraFailCount % 10 == 0 || (ultraReadCount > 0 && ultraFailCount * 100 / ultraReadCount > 20)) {
                Serial.printf("[ULTRA] FAIL #%lu (rate=%.1f%%) speed=%d dir=%d consecutiveTimeouts=%d\n",
                              ultraFailCount,
                              100.0f * ultraFailCount / ultraReadCount,
                              g_currentBaseSpeed,
                              g_currentDirection,
                              us->getConsecutiveTimeouts());
            }
        }
        return (dist < 0) ? -1 : (int16_t)dist;
    }
    return -1;
}

float distanceFront() {
    auto sensor = SensorManager::instance().getSensor(SensorID::Ultrasonic);
    if (sensor) {
        auto us = static_cast<Ultrasonic*>(sensor);
        us->update();
        return us->distanceCm();
    }
    return -1.0f;
}

void Wait(uint32_t ms) {
    Serial.printf("[%lu] Wait : %lu ms\n", millis(), ms);
    delay(ms);
}

// ===== Line Following =====

void LineBasis(int speed) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Line motion blocked: Robot not ready");
        return;
    }
    auto& follower = LineFollower::instance();
    uint8_t mask = static_cast<uint8_t>(GetTraceRaw(1));
    int left, right;
    follower.update(mask, speed, left, right);
    setMotorsDirect(left, right);
}

void LineFollow(int speed) {
    LineBasis(speed);
}

void LineStop() {
    auto& follower = LineFollower::instance();
    follower.stop();
    Stop();
}

void LineIntersectionStop(int speed, int type) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Line motion blocked: Robot not ready");
        return;
    }
    Serial.printf("[Line] LineIntersectionStop speed=%d type=%d\n", speed, type);
    auto& follower = LineFollower::instance();
    follower.setSpeed(speed);
    follower.stopAtIntersection();
    while (!follower.isStopped()) {
        uint8_t mask = static_cast<uint8_t>(GetTraceRaw(1));
        int left, right;
        follower.update(mask, speed, left, right);
        setMotorsDirect(left, right);
        delay(20);
    }
}

void LineTurnEncounterLine(int speed, int angle, int direction) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Line motion blocked: Robot not ready");
        return;
    }
    Serial.printf("[Line] LineTurnEncounterLine speed=%d angle=%d dir=%d\n", speed, angle, direction);
    auto& follower = LineFollower::instance();
    follower.setSpeed(speed);
    follower.turnEncounterLine(direction);
    while (true) {
        uint8_t mask = static_cast<uint8_t>(GetTraceRaw(1));
        int left, right;
        follower.update(mask, speed, left, right);
        setMotorsDirect(left, right);
        if (mask != 0) break;
        delay(20);
    }
}

void LineForBmp(int speed, int degree) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Line motion blocked: Robot not ready");
        return;
    }
    Serial.printf("[Line] LineForBmp speed=%d degree=%d\n", speed, degree);
    auto& follower = LineFollower::instance();
    follower.followForBmp(speed, degree);
    while (follower.isBmpActive()) {
        uint8_t mask = static_cast<uint8_t>(GetTraceRaw(1));
        int left, right;
        follower.update(mask, speed, left, right);
        setMotorsDirect(left, right);
        delay(20);
    }
    Stop();
}

// ===== LED, Servo, MP3, Trace =====

void SetServo(int port, int angle) {
    Serial.printf("[DUMMY][SetServo] port=%d angle=%d\n", port, angle);
}

void Set3CLed(int port, int state) {
    int pin;
    if ((port % 2) == 0) {
        pin = OUTPUT_LED_LEFT_PIN;   // GPIO32
    } else {
        pin = OUTPUT_LED_RIGHT_PIN;  // GPIO33
    }
    digitalWrite(pin, state ? HIGH : LOW);
    Serial.printf("[LED] Set3CLed port=%d -> GPIO%d state=%d\n", port, pin, state);
}

void SetLightSensorLed(int port, int state) {
    Serial.printf("[DUMMY][SetLightSensorLed] port=%d state=%d\n", port, state);
}

void SetMotorStraightAngle(int leftPort, int rightPort, int speed, int angle) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Motion blocked: Robot not ready");
        return;
    }
    Serial.printf("[DUMMY][SetMotorStraightAngle] leftPort=%d rightPort=%d speed=%d angle=%d\n",
                  leftPort, rightPort, speed, angle);
}

void SetMp3Play(int index) {
    Serial.printf("[BUZZER] SetMp3Play index=%d -> fixed beep 200ms\n", index);
    digitalWrite(OUTPUT_BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(OUTPUT_BUZZER_PIN, LOW);
}

int16_t GetTraceValue(int port, int channel) {
    SensorID id;
    switch (channel) {
        case 0: id = SensorID::LineLeft; break;
        case 1: id = SensorID::LineCenter; break;
        case 2: id = SensorID::LineRight; break;
        default: return 0;
    }
    auto sensor = SensorManager::instance().getSensor(id);
    if (sensor) {
        auto lineSensor = static_cast<TCRT5000*>(sensor);
        lineSensor->update();
        return lineSensor->isLineDetected() ? 100 : 0;
    }
    return 0;
}

bool GetTraceState(int port, int channel) {
    SensorID id;
    switch (channel) {
        case 0: id = SensorID::LineLeft; break;
        case 1: id = SensorID::LineCenter; break;
        case 2: id = SensorID::LineRight; break;
        default: return false;
    }
    auto sensor = SensorManager::instance().getSensor(id);
    if (sensor) {
        auto lineSensor = static_cast<TCRT5000*>(sensor);
        lineSensor->update();
        return lineSensor->isLineDetected();
    }
    return false;
}

int16_t GetTraceRaw(int port) {
    int mask = 0;
    auto left = SensorManager::instance().getSensor(SensorID::LineLeft);
    auto center = SensorManager::instance().getSensor(SensorID::LineCenter);
    auto right = SensorManager::instance().getSensor(SensorID::LineRight);
    if (left) {
        auto l = static_cast<TCRT5000*>(left);
        l->update();
        if (l->isLineDetected()) mask |= 4;
    }
    if (center) {
        auto c = static_cast<TCRT5000*>(center);
        c->update();
        if (c->isLineDetected()) mask |= 2;
    }
    if (right) {
        auto r = static_cast<TCRT5000*>(right);
        r->update();
        if (r->isLineDetected()) mask |= 1;
    }
    return mask;
}

// ===== Initialization =====

void Initialize() {
    loadMotionConfigFromStorage();

    pinMode(MOTOR_L_IN1_PIN, OUTPUT);
    pinMode(MOTOR_L_IN2_PIN, OUTPUT);
    pinMode(MOTOR_R_IN3_PIN, OUTPUT);
    pinMode(MOTOR_R_IN4_PIN, OUTPUT);

    digitalWrite(MOTOR_L_IN1_PIN, LOW);
    digitalWrite(MOTOR_L_IN2_PIN, LOW);
    digitalWrite(MOTOR_R_IN3_PIN, LOW);
    digitalWrite(MOTOR_R_IN4_PIN, LOW);

    ledcAttach(MOTOR_L_IN1_PIN, PWM_FREQ, PWM_RES);
    ledcAttach(MOTOR_L_IN2_PIN, PWM_FREQ, PWM_RES);
    ledcAttach(MOTOR_R_IN3_PIN, PWM_FREQ, PWM_RES);
    ledcAttach(MOTOR_R_IN4_PIN, PWM_FREQ, PWM_RES);

    _setMotorsRaw(0, 0);
    Serial.println("[RobotAPI] Motors initialized with MotionConfig.");

    touch0.init();
    touch1.init();

    pinMode(OUTPUT_LED_LEFT_PIN, OUTPUT);
    pinMode(OUTPUT_LED_RIGHT_PIN, OUTPUT);
    digitalWrite(OUTPUT_LED_LEFT_PIN, LOW);
    digitalWrite(OUTPUT_LED_RIGHT_PIN, LOW);
    Serial.println("[RobotAPI] LEDs initialized (OFF)");

    lightSensor.init();
    colorSensor.init();

    auto& mgr = SensorManager::instance();
    mgr.registerSensor(SensorID::LineLeft,
                       new TCRT5000(SENSOR_TRCT5000_L_PIN, "line_left"));
    mgr.registerSensor(SensorID::LineCenter,
                       new TCRT5000(SENSOR_TRCT5000_C_PIN, "line_center"));
    mgr.registerSensor(SensorID::LineRight,
                       new TCRT5000(SENSOR_TRCT5000_R_PIN, "line_right"));
    mgr.registerSensor(SensorID::Ultrasonic,
                       new Ultrasonic(SONIC_TRIG_PIN, SONIC_ECHO_PIN, 30000, "ultrasonic"));

    IMUSensor* imu = new IMUSensor();
    mgr.registerSensor(SensorID::IMU, imu);

    if (!mgr.initializeAll()) {
        Serial.println("[RobotAPI] Some sensors failed to initialize.");
    }

    pinMode(OUTPUT_BUZZER_PIN, OUTPUT);
    digitalWrite(OUTPUT_BUZZER_PIN, LOW);
    Serial.println("[RobotAPI] Buzzer initialized (OFF)");

    loadSensorConfigFromStorage();
    Serial.println("[RobotAPI] Sensors initialized with SensorConfig.");

    _initHeadingController();

    IMUSensor* imuCheck = static_cast<IMUSensor*>(mgr.getSensor(SensorID::IMU));
    if (imuCheck && imuCheck->isReady()) {
        Serial.println("[RobotAPI] IMU sensor is ready.");
    } else {
        Serial.println("[RobotAPI] IMU sensor is NOT ready.");
    }

    // Khởi tạo ultrasonic diagnostic counters
    ultraReadCount = 0;
    ultraFailCount = 0;
}

} // namespace RobotAPI