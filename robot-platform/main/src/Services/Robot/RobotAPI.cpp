/******************************************************************************
 * File        : RobotAPI.cpp
 *
 * Description :
 *      Robot Hardware Abstraction API Implementation.
 *      Supports ESP32 PWM motor control using GPIO pin definitions.
 ******************************************************************************/

#include "RobotAPI.h"
#include "MotionConfig.h"
#include "MotorControlContract.h"
#include "MotorOutputMapper.h"
#include "../../../include/generated/generated_device_config.h"
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
#if ROBOT_FEATURE_IMU
#include "../../Sensor/IMUSensor.h"
#endif

// Line Follower
#include "../../Services/Line/LineFollower.h"

// Heading Estimator & Controller
#include "../../Services/Motion/HeadingEstimator.h"
#include "../../Services/Motion/HeadingController.h"

// VM (for diagnostics)
#include "../../Services/VM/VM.h"
#if ROBOT_FEATURE_ENCODER
#include "../../Devices/Encoder.h"
#endif

// Khai báo HeadingEstimator toàn cục (được định nghĩa trong main.ino)
extern HeadingEstimator g_headingEstimator;
extern bool g_robotReady;
extern VM vm;
// In RobotAPI.cpp, near other static variables:
static bool g_headingDiagnosticEnabled = true;   // ON by default

#if ROBOT_FEATURE_ENCODER
static Encoder leftEncoder(ENCODER_LEFT_A_PIN, ENCODER_LEFT_B_PIN, 1.0f);
static Encoder rightEncoder(ENCODER_RIGHT_A_PIN, ENCODER_RIGHT_B_PIN, 1.0f);
#endif

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
static bool g_headingStartupDiagnosticEnabled = true; 
static bool g_motorPwmDiagnosticEnabled = true;
static bool g_motorMappingDiagnosticEnabled = false;
static int g_lastMotorDiagLogicalLeft = 1000;
static int g_lastMotorDiagLogicalRight = 1000;
static int g_lastMotorDiagMappedLeft = 1000;
static int g_lastMotorDiagMappedRight = 1000;
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
// In RobotAPI.cpp:
void setHeadingDiagnosticEnabled(bool enabled) {
    g_headingDiagnosticEnabled = enabled;
    Serial.printf("[HEADING-DIAG] Heading controller: %s\n",
                  enabled ? "ON" : "OFF");
}

bool isHeadingDiagnosticEnabled() {
    return g_headingDiagnosticEnabled;
}
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
// ---- Motor PWM Diagnostic Functions ----
void setMotorPwmDiagnosticEnabled(bool enabled) {
    g_motorPwmDiagnosticEnabled = enabled;
    Serial.printf("[PWM-DIAG] Motor PWM: %s\n",
                  enabled ? "ON" : "OFF");
}

bool isMotorPwmDiagnosticEnabled() {
    return g_motorPwmDiagnosticEnabled;
}

void setMotorMappingDiagnosticEnabled(bool enabled) {
    g_motorMappingDiagnosticEnabled = enabled;
    g_lastMotorDiagLogicalLeft = 1000;
    g_lastMotorDiagLogicalRight = 1000;
    g_lastMotorDiagMappedLeft = 1000;
    g_lastMotorDiagMappedRight = 1000;
    Serial.printf("[MOTOR-DIAG] Mapping diagnostic: %s\n", enabled ? "ON" : "OFF");
}

bool isMotorMappingDiagnosticEnabled() {
    return g_motorMappingDiagnosticEnabled;
}

// ---- Line Response Latency Diagnostic (H23-D) ----
static bool g_lineResponseDiagnosticEnabled = false;
static uint8_t g_lastLineTraceMask = 0xFF;
static uint32_t g_lastLineBasisUs = 0;

void setLineResponseDiagnosticEnabled(bool enabled) {
    g_lineResponseDiagnosticEnabled = enabled;
    g_lastLineTraceMask = 0xFF;
    g_lastLineBasisUs = 0;
    Serial.printf("[LINE-RESPONSE] Diagnostic: %s\n", enabled ? "ON" : "OFF");
}

bool isLineResponseDiagnosticEnabled() {
    return g_lineResponseDiagnosticEnabled;
}
// ---- Forward declarations ----
static void _stopMotion(StopReason reason = STOP_REASON_COMMAND_STOP);
static void _applyMotion();

// ---- Motor control internal ----
// ---- Heading Startup Diagnostic Functions ----
void setHeadingStartupDiagnosticEnabled(bool enabled) {
    g_headingStartupDiagnosticEnabled = enabled;
    Serial.printf("[HEADING-STARTUP-DIAG] Heading startup: %s\n",
                  enabled ? "ON" : "OFF");
}

bool isHeadingStartupDiagnosticEnabled() {
    return g_headingStartupDiagnosticEnabled;
}
// ---- Modified _setMotorsRaw() ----
static void _setMotorsRaw(int leftSpeed, int rightSpeed) {
    leftSpeed = constrain(leftSpeed, -100, 100);
    rightSpeed = constrain(rightSpeed, -100, 100);

    // Calculate PWM values (always keep calculation for diagnostics)
    int leftPWM = abs(leftSpeed) * g_motionConfig.pwmPerSpeed;
    int rightPWM = abs(rightSpeed) * g_motionConfig.pwmPerSpeed;
    leftPWM = constrain(leftPWM, 0, 255);
    rightPWM = constrain(rightPWM, 0, 255);

    // ---- DIAGNOSTIC: Bypass hardware PWM writes ----
    if (!g_motorPwmDiagnosticEnabled) {
        // Log once per motion session to avoid spam
        static bool loggedOnce = false;
        if (!loggedOnce) {
            Serial.printf("[PWM-DIAG] requested L=%d R=%d, hardware PWM BYPASSED\n",
                          leftSpeed, rightSpeed);
            loggedOnce = true;
        }
        // Set all motor pins to LOW to ensure no PWM output and safe state
        digitalWrite(MOTOR_L_IN1_PIN, LOW);
        digitalWrite(MOTOR_L_IN2_PIN, LOW);
        digitalWrite(MOTOR_R_IN3_PIN, LOW);
        digitalWrite(MOTOR_R_IN4_PIN, LOW);
        return;
    }
    // ---- END DIAGNOSTIC ----

    // ---- NORMAL PWM OUTPUT (existing code) ----
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

// H23-A ownership boundary:
// All public motion callers provide LOGICAL commands in [-100, 100].
// This function is the single owner of speedScale and per-motor calibration.
// Callers must never pre-apply calibration before reaching this boundary.
static void _setMotors(int leftSpeed, int rightSpeed) {
    const int logicalLeft = clampLogicalMotorCommand(leftSpeed);
    const int logicalRight = clampLogicalMotorCommand(rightSpeed);

    const int mappedLeft = MotorOutputMapper::map(
        logicalLeft,
        g_motionConfig.speedScale,
        g_motionConfig.leftMotorScale,
        g_motionConfig.minSpeed
    );
    const int mappedRight = MotorOutputMapper::map(
        logicalRight,
        g_motionConfig.speedScale,
        g_motionConfig.rightMotorScale,
        g_motionConfig.minSpeed
    );

    if (g_motorMappingDiagnosticEnabled &&
        (logicalLeft != g_lastMotorDiagLogicalLeft ||
         logicalRight != g_lastMotorDiagLogicalRight ||
         mappedLeft != g_lastMotorDiagMappedLeft ||
         mappedRight != g_lastMotorDiagMappedRight)) {
        const int pwmLeft = (int)(abs(mappedLeft) * g_motionConfig.pwmPerSpeed);
        const int pwmRight = (int)(abs(mappedRight) * g_motionConfig.pwmPerSpeed);
        Serial.printf(
            "[MOTOR-DIAG] logical L=%d R=%d | scale global=%.3f L=%.3f R=%.3f | minDrive=%d | mapped L=%d R=%d | pwm L=%d R=%d\n",
            logicalLeft, logicalRight,
            g_motionConfig.speedScale,
            g_motionConfig.leftMotorScale,
            g_motionConfig.rightMotorScale,
            g_motionConfig.minSpeed,
            mappedLeft, mappedRight,
            pwmLeft, pwmRight
        );
        g_lastMotorDiagLogicalLeft = logicalLeft;
        g_lastMotorDiagLogicalRight = logicalRight;
        g_lastMotorDiagMappedLeft = mappedLeft;
        g_lastMotorDiagMappedRight = mappedRight;
    }

    _setMotorsRaw(mappedLeft, mappedRight);
}

// ---- Heading Hold Controller ----
static HeadingController g_headingController;

enum class MotionControlMode : uint8_t {
    None = 0,
    Heading,
    Line,
};

static MotionControlMode g_motionControlMode = MotionControlMode::None;
static bool g_headingHoldEnabled = true;
static bool g_isMoving = false;
static int g_currentBaseSpeed = 0;
static int g_currentDirection = 0;
static int g_effectiveLeft = 0;
static int g_effectiveRight = 0;
// ---- H15: Motion/Ultrasonic correlation diagnostics ----
static uint32_t g_motionSessionId = 0;
static uint32_t g_motionStartMs = 0;
// ---- DEBUG-H2-001: Motion Output Diagnostic Flag ----
static bool g_motionOutputDiagnosticEnabled = true; 
// ---- Ultrasonic Diagnostic Counters ----
static uint32_t ultraReadCount = 0;
static uint32_t ultraFailCount = 0;

// ---- Stop Motion (with reason) ----
static void _stopMotion(StopReason reason) {
    if (g_isMoving) {
        Serial.printf("[MOTION-ULTRA-CORR] STOP session=%lu t=%lu age=%lu reason=%s\n",
                      (unsigned long)g_motionSessionId,
                      (unsigned long)millis(),
                      (unsigned long)(millis() - g_motionStartMs),
                      stopReasonToString(reason));
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
    g_motionControlMode = MotionControlMode::None;
    g_headingController.stop();
    _setMotorsRaw(0, 0);
    g_effectiveLeft = 0;
    g_effectiveRight = 0;
}
// ---- Motion Control Ownership ----
// Line following owns steering exclusively through the line sensors.  IMU may
// continue updating in the background, but HeadingController must not be
// allowed to write motor corrections while LINE mode is active.
static void _enterLineControlMode() {
    if (g_motionControlMode != MotionControlMode::Line) {
        Serial.println("[MOTION-MODE] LINE: heading control disabled, line sensors own motor steering");
    }

    g_isMoving = false;
    g_headingController.stop();
    g_currentBaseSpeed = 0;
    g_currentDirection = 0;
    g_effectiveLeft = 0;
    g_effectiveRight = 0;
    g_motionControlMode = MotionControlMode::Line;
}

// ---- Motion Output Diagnostic Functions ----
void setMotionOutputDiagnosticEnabled(bool enabled) {
    g_motionOutputDiagnosticEnabled = enabled;
    Serial.printf("[MOTION-DIAG] Motion output: %s\n",
                  enabled ? "ON" : "OFF");
}

bool isMotionOutputDiagnosticEnabled() {
    return g_motionOutputDiagnosticEnabled;
}
// ---- Modified _applyMotion() ----
static void _applyMotion() {
    // Only HEADING mode is allowed to run the IMU/heading motor loop.
    if (g_motionControlMode != MotionControlMode::Heading || !g_isMoving) {
        _setMotorsRaw(0, 0);
        g_effectiveLeft = 0;
        g_effectiveRight = 0;
        return;
    }

    int baseSpeed = g_currentBaseSpeed;
    int direction = g_currentDirection;

    // ---- DIAGNOSTIC: Motion Output Gate ----
    // When OFF, keep motion state/heading processing active but block all
    // physical motor output. This is intentionally different from the
    // low-level "motor pwm" diagnostic, which gates _setMotorsRaw() itself.
    if (!g_motionOutputDiagnosticEnabled) {
        int left = (direction > 0) ? baseSpeed : -baseSpeed;
        int right = (direction > 0) ? baseSpeed : -baseSpeed;

        g_effectiveLeft = left;
        g_effectiveRight = right;

        static bool loggedOnce = false;
        if (!loggedOnce) {
            Serial.printf("[MOTION-DIAG] Physical motor output BLOCKED: requested L=%d R=%d\n",
                          left, right);
            loggedOnce = true;
        }
        return;
    }
    // ---- END DIAGNOSTIC ----

    // ---- NORMAL PATH (existing code) ----
    float correction = 0.0f;

    // Existing heading correction logic (unchanged)
#if ROBOT_FEATURE_IMU
    if (g_headingDiagnosticEnabled && g_headingHoldEnabled && g_headingController.isActive()) {
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
#endif

    // H23-B: heading control produces logical commands only. Calibration,
    // minimum-drive mapping and PWM conversion are owned by _setMotors().
    int leftCommand, rightCommand;
    if (direction < 0) {
        leftCommand = -baseSpeed - (int)correction;
        rightCommand = -baseSpeed + (int)correction;
    } else {
        leftCommand = baseSpeed - (int)correction;
        rightCommand = baseSpeed + (int)correction;
    }

    leftCommand = clampLogicalMotorCommand(leftCommand);
    rightCommand = clampLogicalMotorCommand(rightCommand);

    g_effectiveLeft = leftCommand;
    g_effectiveRight = rightCommand;

    _setMotors(leftCommand, rightCommand);

    // Optional heading diagnostic log (unchanged)
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
    g_motionControlMode = MotionControlMode::None;
    g_currentBaseSpeed = 0;
    g_currentDirection = 0;
    g_effectiveLeft = 0;
    g_effectiveRight = 0;
    _setMotorsRaw(0, 0);
    Serial.println("[RobotAPI] Heading controller reset");
}

// ---- Modified _startMotion() ----
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

    // Explicit ownership transition: normal forward/backward motion is
    // controlled by the heading controller, not by any previous line mode.
    g_motionControlMode = MotionControlMode::Heading;
    g_currentBaseSpeed = speed;
    g_currentDirection = direction;
    g_isMoving = true;

    if (newSession) {
        ++g_motionSessionId;
        g_motionStartMs = millis();
        Serial.printf("[MOTION-ULTRA-CORR] START session=%lu t=%lu direction=%d speed=%d\n",
                      (unsigned long)g_motionSessionId,
                      (unsigned long)g_motionStartMs,
                      direction,
                      speed);
        Serial.printf("[HEADING-STARTUP-DIAG] StartMotion direction=%d speed=%d\n",
                      direction, speed);

        // Heading startup must honor the public heading diagnostic switch.
        // If "heading off" is active, do not initialize or start the controller.
        if (g_headingDiagnosticEnabled && g_headingStartupDiagnosticEnabled) {
            // ---- NORMAL PATH: Heading initialization enabled ----
            Serial.println("[HEADING-STARTUP-DIAG] Heading startup: ENABLED");
            g_headingController.reset();

#if ROBOT_FEATURE_IMU
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
#else
            g_headingController.stop();
            Serial.println("[Heading] Heading hold unavailable (ROBOT_FEATURE_IMU=0)");
#endif
        } else {
            // ---- DIAGNOSTIC PATH: Heading startup BYPASSED ----
            Serial.println("[HEADING-STARTUP-DIAG] Heading startup: BYPASSED");
            // Do NOT reset or start HeadingController.
            // Ensure controller is stopped to avoid any residual correction.
            g_headingController.stop();
        }
    } else {
        // Motion continues from previous session; maintain heading hold if already active
#if ROBOT_FEATURE_IMU
        if (g_headingDiagnosticEnabled && g_headingHoldEnabled && !g_headingController.isActive()) {
            auto* imu = static_cast<IMUSensor*>(SensorManager::instance().getSensor(SensorID::IMU));
            if (imu && imu->isReady() && imu->isCalibrated()) {
                g_headingController.start(g_headingController.getTargetHeading());
                Serial.printf("[Heading] CONTROLLER RESTART (target=%.2f deg)\n",
                              g_headingController.getTargetHeading());
            }
        }
#endif
    }

    _applyMotion();

    if (newSession) {
        Serial.printf("[MOTION-ULTRA-CORR] ACTIVE session=%lu t=%lu age=%lu moving=%d effL=%d effR=%d pwm=%d output=%d\n",
                      (unsigned long)g_motionSessionId,
                      (unsigned long)millis(),
                      (unsigned long)(millis() - g_motionStartMs),
                      g_isMoving ? 1 : 0,
                      g_effectiveLeft,
                      g_effectiveRight,
                      g_motorPwmDiagnosticEnabled ? 1 : 0,
                      g_motionOutputDiagnosticEnabled ? 1 : 0);
    }
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
    if (g_motionControlMode == MotionControlMode::Heading && g_isMoving && g_robotReady) {
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

    const uint32_t readSeq = ultraReadCount;
    const uint32_t readStartMs = millis();
    const uint32_t sessionAtStart = g_motionSessionId;
    const bool movingAtStart = g_isMoving;
    const uint32_t motionAgeAtStart = movingAtStart ? (readStartMs - g_motionStartMs) : 0;

    Serial.printf(
        "[MOTION-ULTRA-CORR] READ-BEGIN seq=%lu t=%lu session=%lu age=%lu "
        "moving=%d speed=%d dir=%d effL=%d effR=%d\n",
        (unsigned long)readSeq,
        (unsigned long)readStartMs,
        (unsigned long)sessionAtStart,
        (unsigned long)motionAgeAtStart,
        movingAtStart ? 1 : 0,
        g_currentBaseSpeed,
        g_currentDirection,
        g_effectiveLeft,
        g_effectiveRight
    );

    auto sensor = SensorManager::instance().getSensor(SensorID::Ultrasonic);
    if (!sensor) {
        ultraFailCount++;
        Serial.printf(
            "[ULTRA-DIAG] t=%lu seq=%lu result=-1 sensor=NULL speed=%d dir=%d fails=%lu\n",
            millis(),
            (unsigned long)readSeq,
            g_currentBaseSpeed,
            g_currentDirection,
            (unsigned long)ultraFailCount
        );
        return -1;
    }

    auto us = static_cast<Ultrasonic*>(sensor);

    // Keep the existing sensor read path unchanged.
    us->update();
    float dist = us->distanceCm();

    const uint32_t readEndMs = millis();
    const uint32_t readElapsedMs = readEndMs - readStartMs;
    const uint32_t sessionAtEnd = g_motionSessionId;
    const bool movingAtEnd = g_isMoving;
    const uint32_t motionAgeAtEnd = movingAtEnd ? (readEndMs - g_motionStartMs) : 0;

    Serial.printf(
        "[MOTION-ULTRA-CORR] READ-END seq=%lu t=%lu elapsed=%lu "
        "session=%lu sessionChanged=%d age=%lu moving=%d speed=%d dir=%d effL=%d effR=%d\n",
        (unsigned long)readSeq,
        (unsigned long)readEndMs,
        (unsigned long)readElapsedMs,
        (unsigned long)sessionAtEnd,
        sessionAtEnd != sessionAtStart ? 1 : 0,
        (unsigned long)motionAgeAtEnd,
        movingAtEnd ? 1 : 0,
        g_currentBaseSpeed,
        g_currentDirection,
        g_effectiveLeft,
        g_effectiveRight
    );

    if (dist < 0) {
        ultraFailCount++;
        Serial.printf(
            "[ULTRA-DIAG] t=%lu seq=%lu result=-1 status=TIMEOUT "
            "speed=%d dir=%d consecutiveTimeouts=%d failCount=%lu failRate=%.1f%% healthy=%s\n",
            readEndMs,
            (unsigned long)readSeq,
            g_currentBaseSpeed,
            g_currentDirection,
            us->getConsecutiveTimeouts(),
            (unsigned long)ultraFailCount,
            100.0f * ultraFailCount / ultraReadCount,
            us->healthy() ? "YES" : "NO"
        );
        return -1;
    }

    Serial.printf(
        "[ULTRA-DIAG] t=%lu seq=%lu result=%.1fcm status=OK "
        "speed=%d dir=%d consecutiveTimeouts=%d healthy=%s\n",
        readEndMs,
        (unsigned long)readSeq,
        dist,
        g_currentBaseSpeed,
        g_currentDirection,
        us->getConsecutiveTimeouts(),
        us->healthy() ? "YES" : "NO"
    );

    return (int16_t)dist;
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

    const uint32_t t0 = micros();
    const uint32_t loopDtUs = (g_lastLineBasisUs == 0) ? 0 : (uint32_t)(t0 - g_lastLineBasisUs);
    g_lastLineBasisUs = t0;

    _enterLineControlMode();
    auto& follower = LineFollower::instance();

    const uint32_t sensorStartUs = micros();
    uint8_t mask = static_cast<uint8_t>(GetTraceRaw(1));
    const uint32_t sensorDoneUs = micros();

    int left = 0;
    int right = 0;
    follower.update(mask, speed, left, right);
    const uint32_t controlDoneUs = micros();

    setMotorsDirect(left, right);
    const uint32_t outputDoneUs = micros();

    // Change-triggered: logs the exact synchronous software path for a new line state.
    // totalUs measures sensor sampling -> follower decision -> motor API/PWM submission.
    if (g_lineResponseDiagnosticEnabled && mask != g_lastLineTraceMask) {
        const uint8_t previous = g_lastLineTraceMask;
        Serial.printf(
            "[LINE-RESPONSE] t=%luus mask=%03u prev=%s loop=%luus | sensor=%luus control=%luus output=%luus total=%luus | cmd L=%d R=%d\n",
            (unsigned long)t0,
            (unsigned)mask,
            (previous == 0xFF) ? "---" : String(previous).c_str(),
            (unsigned long)loopDtUs,
            (unsigned long)(sensorDoneUs - sensorStartUs),
            (unsigned long)(controlDoneUs - sensorDoneUs),
            (unsigned long)(outputDoneUs - controlDoneUs),
            (unsigned long)(outputDoneUs - sensorStartUs),
            left,
            right
        );
        g_lastLineTraceMask = mask;
    }
}

void LineFollow(int speed) {
    LineBasis(speed);
}

void LineMillisecond(int speed, int millisecond) {
    if (!g_robotReady) {
        Serial.println("[RobotAPI] Line motion blocked: Robot not ready");
        return;
    }

    _enterLineControlMode();

    if (millisecond <= 0) {
        Stop();
        return;
    }

    Serial.printf("[Line] LineMillisecond speed=%d duration=%dms\\n",
                  speed, millisecond);

    auto& follower = LineFollower::instance();
    const uint32_t start = millis();

    follower.setSpeed(speed);
    follower.reset();

    while ((uint32_t)(millis() - start) < (uint32_t)millisecond) {
        uint8_t mask = static_cast<uint8_t>(GetTraceRaw(1));
        int left = 0;
        int right = 0;

        follower.update(mask, speed, left, right);
        setMotorsDirect(left, right);
        delay(20);
    }

    follower.stop();
    Stop();
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

    _enterLineControlMode();
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

    _enterLineControlMode();
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

    _enterLineControlMode();
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


#if ROBOT_FEATURE_ENCODER
void UpdateEncoders() { leftEncoder.update(); rightEncoder.update(); }
static Encoder& encoderBySide(int side) { return side == 0 ? leftEncoder : rightEncoder; }
int64_t GetEncoderCount(int side) { return encoderBySide(side).getCount(); }
float GetEncoderCountsPerSecond(int side) { return encoderBySide(side).getCountsPerSecond(); }
float GetEncoderRPM(int side) { return encoderBySide(side).getRPM(); }
void ResetEncoderCount(int side, int64_t value) { encoderBySide(side).resetCount(value); }
void SetEncoderCountsPerRevolution(int side, float value) { encoderBySide(side).setCountsPerRevolution(value); }
float GetEncoderCountsPerRevolution(int side) { return encoderBySide(side).getCountsPerRevolution(); }
void SetEncoderInverted(int side, bool inverted) { encoderBySide(side).setInverted(inverted); }
bool GetEncoderInverted(int side) { return encoderBySide(side).isInverted(); }
#else
void UpdateEncoders() {}
int64_t GetEncoderCount(int side) { (void)side; return 0; }
float GetEncoderCountsPerSecond(int side) { (void)side; return 0.0f; }
float GetEncoderRPM(int side) { (void)side; return 0.0f; }
void ResetEncoderCount(int side, int64_t value) { (void)side; (void)value; }
void SetEncoderCountsPerRevolution(int side, float value) { (void)side; (void)value; }
float GetEncoderCountsPerRevolution(int side) { (void)side; return 0.0f; }
void SetEncoderInverted(int side, bool inverted) { (void)side; (void)inverted; }
bool GetEncoderInverted(int side) { (void)side; return false; }
#endif

void Initialize() {
#if ROBOT_FEATURE_ENCODER
    leftEncoder.begin();
    rightEncoder.begin();
    Serial.println("[RobotAPI] Encoders enabled and initialized.");
#else
    Serial.println("[RobotAPI] Encoders disabled by hardware configuration.");
#endif

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
                       new Ultrasonic(SONIC_TRIG_PIN, SONIC_ECHO_PIN, 50000, "ultrasonic"));

#if ROBOT_FEATURE_IMU
    IMUSensor* imu = new IMUSensor();
    mgr.registerSensor(SensorID::IMU, imu);
#endif

    if (!mgr.initializeAll()) {
        Serial.println("[RobotAPI] Some sensors failed to initialize.");
    }

    pinMode(OUTPUT_BUZZER_PIN, OUTPUT);
    digitalWrite(OUTPUT_BUZZER_PIN, LOW);
    Serial.println("[RobotAPI] Buzzer initialized (OFF)");

    loadSensorConfigFromStorage();
    Serial.println("[RobotAPI] Sensors initialized with SensorConfig.");

#if ROBOT_FEATURE_IMU
    _initHeadingController();

    IMUSensor* imuCheck = static_cast<IMUSensor*>(mgr.getSensor(SensorID::IMU));
    if (imuCheck && imuCheck->isReady()) {
        Serial.println("[RobotAPI] IMU sensor is ready.");
    } else {
        Serial.println("[RobotAPI] IMU sensor is NOT ready.");
    }
#else
    g_headingController.stop();
    g_headingHoldEnabled = false;
    Serial.println("[RobotAPI] IMU disabled by hardware configuration; heading hold is unavailable.");
#endif

    // Khởi tạo ultrasonic diagnostic counters
    ultraReadCount = 0;
    ultraFailCount = 0;
}

} // namespace RobotAPI
