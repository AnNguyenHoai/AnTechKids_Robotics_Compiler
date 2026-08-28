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
#include "../../Devices/Ultrasonic.h"
#include "../../Devices/Touch.h"
#include "../../Devices/LineSensor.h"
#include "../../Devices/LightSensor.h"
#include "../../Devices/ColorSensor.h"
#include "../../Devices/Encoder.h"
#include "../../Devices/SensorConfig.h"
#include "../../HardwareAbstraction/GPIO.h"

namespace RobotAPI {

// Cấu hình PWM cho ESP32
#define PWM_FREQ 5000
#define PWM_RES 8 // 0-255

// Kênh PWM: dùng 4 kênh cho 4 chân điều khiển
// Left: IN1 (kênh 0), IN2 (kênh 1)
// Right: IN3 (kênh 2), IN4 (kênh 3)
static const int PWM_CH_L_IN1 = 0;
static const int PWM_CH_L_IN2 = 1;
static const int PWM_CH_R_IN3 = 2;
static const int PWM_CH_R_IN4 = 3;

// Định nghĩa các đối tượng cảm biến (toàn cục trong namespace)
static Ultrasonic ultrasonic(SONIC_TRIG_PIN, SONIC_ECHO_PIN);
static Touch touch0(ROBOT_PIN_5);     // ví dụ
static Touch touch1(ROBOT_PIN_14);    // ví dụ
static LineSensor lineSensor(SENSOR_TRCT5000_L_PIN, SENSOR_TRCT5000_C_PIN, SENSOR_TRCT5000_R_PIN);
static LightSensor lightSensor(ROBOT_PIN_32); // ví dụ
static ColorSensor colorSensor;
// H24-D: runtime CPR starts at 1 until physical calibration freezes the value.
static Encoder leftEncoder(ENCODER_LEFT_A_PIN, ENCODER_LEFT_B_PIN, 1.0f);
static Encoder rightEncoder(ENCODER_RIGHT_A_PIN, ENCODER_RIGHT_B_PIN, 1.0f);

// Hàm nội bộ: điều khiển motor
static void _setMotors(int leftSpeed, int rightSpeed) {
    // Áp dụng cấu hình
    leftSpeed = (int)(leftSpeed * g_motionConfig.speedScale * g_motionConfig.leftMotorScale);
    rightSpeed = (int)(rightSpeed * g_motionConfig.speedScale * g_motionConfig.rightMotorScale);

    // Giới hạn
    leftSpeed = constrain(leftSpeed, -100, 100);
    rightSpeed = constrain(rightSpeed, -100, 100);

    int leftPWM = abs(leftSpeed) * g_motionConfig.pwmPerSpeed;
    int rightPWM = abs(rightSpeed) * g_motionConfig.pwmPerSpeed;
    leftPWM = constrain(leftPWM, 0, 255);
    rightPWM = constrain(rightPWM, 0, 255);

    // Điều khiển động cơ trái
    if (leftSpeed >= 0) {
        ledcWrite(MOTOR_L_IN1_PIN, leftPWM);
        ledcWrite(MOTOR_L_IN2_PIN, 0);
    } else {
        ledcWrite(MOTOR_L_IN1_PIN, 0);
        ledcWrite(MOTOR_L_IN2_PIN, leftPWM);
    }

    if (rightSpeed >= 0) {
        Serial.println("RIGHT FORWARD");
        ledcWrite(MOTOR_R_IN3_PIN, rightPWM);
        ledcWrite(MOTOR_R_IN4_PIN, 0);
    } else {
        ledcWrite(MOTOR_R_IN3_PIN, 0);
        ledcWrite(MOTOR_R_IN4_PIN, rightPWM);
    }
}

void setMotorsDirect(int left, int right) {
    _setMotors(left, right);
}

/******************************************************************************
 * Initialization
 ******************************************************************************/

void Initialize() {
    // Load motion config
    loadMotionConfigFromStorage();

    // Pin setup cho motor
    pinMode(MOTOR_L_IN1_PIN, OUTPUT);
    pinMode(MOTOR_L_IN2_PIN, OUTPUT);
    pinMode(MOTOR_R_IN3_PIN, OUTPUT);
    pinMode(MOTOR_R_IN4_PIN, OUTPUT);

    // PWM setup
    ledcAttach(MOTOR_L_IN1_PIN, PWM_FREQ, PWM_RES);
    ledcAttach(MOTOR_L_IN2_PIN, PWM_FREQ, PWM_RES);
    ledcAttach(MOTOR_R_IN3_PIN, PWM_FREQ, PWM_RES);
    ledcAttach(MOTOR_R_IN4_PIN, PWM_FREQ, PWM_RES);

    _setMotors(0, 0);
    Serial.println("[RobotAPI] Motors initialized with MotionConfig.");

    // Khởi tạo cảm biến
    ultrasonic.init();
    touch0.init();
    touch1.init();
    lineSensor.init();
    lightSensor.init();
    colorSensor.init();
    leftEncoder.begin();
    rightEncoder.begin();
    Serial.println("[RobotAPI] H24-D encoders initialized (GPIO34/35 left, GPIO36/39 right).");

    // Load sensor config
    loadSensorConfigFromStorage();
    Serial.println("[RobotAPI] Sensors initialized with SensorConfig.");

}


/******************************************************************************
 * Encoder (H24-D physical bring-up)
 ******************************************************************************/
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

/******************************************************************************
 * Motion Control
 ******************************************************************************/

void Forward(int16_t speed) {
    Serial.printf("[%lu] Forward : %d\n", millis(), speed);
    _setMotors(speed, speed);
}

void Backward(int16_t speed) {
    Serial.printf("[%lu] Backward : %d\n", millis(), speed);
    _setMotors(-speed, -speed);
}

void TurnLeft(int16_t speed) {
    Serial.printf("[%lu] TurnLeft : %d\n", millis(), speed);
    _setMotors(-speed * g_motionConfig.turnCompensation, speed * g_motionConfig.turnCompensation);
}

void TurnRight(int16_t speed) {
    Serial.printf("[%lu] TurnRight : %d\n", millis(), speed);
    _setMotors(speed * g_motionConfig.turnCompensation, -speed * g_motionConfig.turnCompensation);
}

void Stop() {
    Serial.printf("[%lu] Stop\n", millis());
    _setMotors(0, 0);
}

/******************************************************************************
 * Sensor
 ******************************************************************************/

int16_t ReadUltrasonic() {
    int distance = ultrasonic.readDistance();
    Serial.printf("[%lu] ReadUltrasonic: %d cm\n", millis(), distance);
    return distance;
}

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
    bool val = false;
    if (channel == 0) val = lineSensor.readLeft();
    else if (channel == 1) val = lineSensor.readCenter();
    else if (channel == 2) val = lineSensor.readRight();
    if (g_sensorConfig.lineInverted) val = !val;
    Serial.printf("[%lu] ReadLine ch %d: %d\n", millis(), channel, val);
    return val ? 1 : 0;
}

/******************************************************************************
 * Utility
 ******************************************************************************/

void Wait(uint16_t ms) {
    Serial.printf("[%lu] Wait : %d ms\n", millis(), ms);
    delay(ms);
}

} // namespace RobotAPI