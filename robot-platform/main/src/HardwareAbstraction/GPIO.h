#ifndef GPIO_H
#define GPIO_H

#include "Arduino.h"
#include "BoardProfile.h"

// Generic raw pin constants retained for legacy code that is not yet migrated.
#define ROBOT_PIN_5     5
#define ROBOT_PIN_13    13
#define ROBOT_PIN_14    14
#define ROBOT_PIN_16    16
#define ROBOT_PIN_17    17
#define ROBOT_PIN_18    18
#define ROBOT_PIN_19    19
#define ROBOT_PIN_21    21
#define ROBOT_PIN_22    22
#define ROBOT_PIN_23    23
#define ROBOT_PIN_25    25
#define ROBOT_PIN_26    26
#define ROBOT_PIN_27    27
#define ROBOT_PIN_32    32
#define ROBOT_PIN_33    33
#define ROBOT_PIN_34    34
#define ROBOT_PIN_35    35
#define ROBOT_PIN_36    36
#define ROBOT_PIN_39    39

// ---------------------------------------------------------------------------
// V2 physical wiring compatibility facade.
// BoardProfile.h is the single source of truth. These aliases keep existing
// firmware call sites source-compatible while V2 peripherals are migrated.
// ---------------------------------------------------------------------------

#define MOTOR_SAFE_EN_PIN       BoardProfile::Pins::MOTOR_SAFE_EN

#define SYSTEM_I2C_SCL_PIN      BoardProfile::Pins::SYSTEM_I2C_SCL
#define SYSTEM_I2C_SDA_PIN      BoardProfile::Pins::SYSTEM_I2C_SDA

#define MOTOR_L_IN1_PIN         BoardProfile::Pins::MOTOR_L_IN1
#define MOTOR_L_IN2_PIN         BoardProfile::Pins::MOTOR_L_IN2
#define MOTOR_R_IN3_PIN         BoardProfile::Pins::MOTOR_R_IN3
#define MOTOR_R_IN4_PIN         BoardProfile::Pins::MOTOR_R_IN4

#define SERVO_1_PIN             BoardProfile::Pins::SERVO1
#define SERVO_2_PIN             BoardProfile::Pins::SERVO2

#define SONIC_ECHO_PIN          BoardProfile::Pins::ULTRASONIC_ECHO
#define SONIC_TRIG_PIN          BoardProfile::Pins::ULTRASONIC_TRIG

#define BATTERY_ADC_PIN         BoardProfile::Pins::BATTERY_ADC
#define START_ARM_PIN           BoardProfile::Pins::START_ARM

#define ENCODER_LEFT_A_PIN      BoardProfile::Pins::ENCODER_L_A
#define ENCODER_LEFT_B_PIN      BoardProfile::Pins::ENCODER_L_B
#define ENCODER_RIGHT_A_PIN     BoardProfile::Pins::ENCODER_R_A
#define ENCODER_RIGHT_B_PIN     BoardProfile::Pins::ENCODER_R_B

#define MCP23017_I2C_ADDRESS    BoardProfile::MCP23017::ADDRESS

// MPU6050 is a System-I2C consumer on V2. V2-SW-002 will move Wire ownership
// into the shared bus manager; these aliases already point at the fixed bus.
#define MPU6050_SDA_PIN         BoardProfile::Pins::SYSTEM_I2C_SDA
#define MPU6050_SCL_PIN         BoardProfile::Pins::SYSTEM_I2C_SCL

// Legacy direct GPIO output aliases. V2-SW-008 migrates these outputs to
// MCP23017 Port B; they are intentionally excluded from BoardProfile V2 pins.
#define OUTPUT_BUZZER_PIN       ROBOT_PIN_19
#define OUTPUT_LED_LEFT_PIN     ROBOT_PIN_32
#define OUTPUT_LED_RIGHT_PIN    ROBOT_PIN_33

#endif
