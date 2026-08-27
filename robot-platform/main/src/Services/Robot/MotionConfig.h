#pragma once

#include <stdint.h>

namespace RobotAPI {

/**
 * Motion Configuration parameters.
 * Used to calibrate robot without recompiling.
 */
struct MotionConfig {
    // Wheel parameters
    float wheelDiameter_mm = 65.0f;
    float wheelBase_mm = 140.0f;

    // Speed calibration
    float speedScale = 1.0f;
    float leftMotorScale = 1.0f;
    float rightMotorScale = 1.0f;

    // Limits
    int minSpeed = 65;  // H23-B minimum physical drive; 0 remains true stop
    int maxSpeed = 100;

    // Turn compensation (multiplier for turning speeds)
    float turnCompensation = 1.0f;

    // PWM mapping
    float pwmPerSpeed = 2.55f;  // 255/100
};

// Global config instance
extern MotionConfig g_motionConfig;

// Load default config
void loadDefaultMotionConfig();

// Load from storage (placeholder)
void loadMotionConfigFromStorage();

// Save to storage (placeholder)
void saveMotionConfigToStorage();

} // namespace RobotAPI

// Safe limits for motor scales (outside namespace for easy use in SerialCommandHandler)
constexpr float MIN_MOTOR_SCALE = 0.50f;
constexpr float MAX_MOTOR_SCALE = 1.50f;