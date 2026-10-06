#pragma once

#include <stdint.h>

/**
 * V2-SW-001 — Board Profile Contract.
 *
 * This file is the authoritative software representation of the fixed
 * AnTech Robot V2 physical wiring. Feature configuration must never remap
 * these values; HardwareConfig only enables/disables capabilities.
 */
namespace BoardProfile {

constexpr const char* ID = "antech_robot_v2";
constexpr const char* REVISION = "v2";

namespace Pins {
constexpr uint8_t MOTOR_SAFE_EN = 4;

constexpr uint8_t SYSTEM_I2C_SCL = 13;
constexpr uint8_t SYSTEM_I2C_SDA = 21;

constexpr uint8_t MOTOR_R_IN4 = 14;
constexpr uint8_t MOTOR_L_IN1 = 25;
constexpr uint8_t MOTOR_L_IN2 = 26;
constexpr uint8_t MOTOR_R_IN3 = 27;

constexpr uint8_t SERVO1 = 16;
constexpr uint8_t SERVO2 = 17;

constexpr uint8_t ULTRASONIC_ECHO = 22;
constexpr uint8_t ULTRASONIC_TRIG = 23;

constexpr uint8_t BATTERY_ADC = 32;
constexpr uint8_t START_ARM = 33;

constexpr uint8_t ENCODER_L_A = 34;
constexpr uint8_t ENCODER_L_B = 35;
constexpr uint8_t ENCODER_R_A = 36;
constexpr uint8_t ENCODER_R_B = 39;
} // namespace Pins

namespace SystemI2C {
constexpr uint32_t INITIAL_FREQUENCY_HZ = 400000;
} // namespace SystemI2C

namespace MCP23017 {
constexpr uint8_t ADDRESS = 0x20;

namespace PortA {
constexpr uint8_t LINE_FAR_LEFT = 0;
constexpr uint8_t LINE_LEFT = 1;
constexpr uint8_t LINE_CENTER = 2;
constexpr uint8_t LINE_RIGHT = 3;
constexpr uint8_t LINE_FAR_RIGHT = 4;
} // namespace PortA

namespace PortB {
constexpr uint8_t LED_LEFT = 0;
constexpr uint8_t LED_RIGHT = 1;
constexpr uint8_t BUZZER_CTRL = 2;
} // namespace PortB
} // namespace MCP23017

} // namespace BoardProfile
