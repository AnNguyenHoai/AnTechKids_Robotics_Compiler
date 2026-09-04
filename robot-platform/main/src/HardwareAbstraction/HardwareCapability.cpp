#include "HardwareCapability.h"
#include "../../include/generated/generated_device_config.h"
#include <Arduino.h>

namespace HardwareCapability {

bool isEnabled(Device device) {
    switch (device) {
        case Device::Motor:       return ROBOT_FEATURE_MOTOR != 0;
        case Device::Encoder:     return ROBOT_FEATURE_ENCODER != 0;
        case Device::LineSensor:  return ROBOT_FEATURE_LINE_SENSOR != 0;
        case Device::Ultrasonic:  return ROBOT_FEATURE_ULTRASONIC != 0;
        case Device::IMU:         return ROBOT_FEATURE_IMU != 0;
        case Device::Servo:       return ROBOT_FEATURE_SERVO != 0;
        case Device::Buzzer:      return ROBOT_FEATURE_BUZZER != 0;
        default:                  return false;
    }
}

const char* name(Device device) {
    switch (device) {
        case Device::Motor:       return "motor";
        case Device::Encoder:     return "encoder";
        case Device::LineSensor:  return "line_sensor";
        case Device::Ultrasonic:  return "ultrasonic";
        case Device::IMU:         return "imu";
        case Device::Servo:       return "servo";
        case Device::Buzzer:      return "buzzer";
        default:                  return "unknown";
    }
}

uint8_t mask() {
    uint8_t result = 0;
    for (uint8_t i = 0; i < static_cast<uint8_t>(Device::Count); ++i) {
        if (isEnabled(static_cast<Device>(i))) {
            result |= static_cast<uint8_t>(1u << i);
        }
    }
    return result;
}

void printStatus() {
    Serial.println("--- Hardware Capability Contract ---");
    for (uint8_t i = 0; i < static_cast<uint8_t>(Device::Count); ++i) {
        const Device device = static_cast<Device>(i);
        Serial.printf("  %-12s : %s\n", name(device),
                      isEnabled(device) ? "ENABLED" : "DISABLED");
    }
    Serial.printf("  mask         : 0x%02X\n", mask());
    Serial.println("------------------------------------");
}

} // namespace HardwareCapability
