#include "MotionConfig.h"

namespace RobotAPI {

MotionConfig g_motionConfig;

void loadDefaultMotionConfig() {
    g_motionConfig.wheelDiameter_mm = 65.0f;
    g_motionConfig.wheelBase_mm = 140.0f;
    g_motionConfig.speedScale = 1.0f;
    g_motionConfig.leftMotorScale = 1.0f;
    g_motionConfig.rightMotorScale = 1.0f;
    g_motionConfig.minSpeed = 0;
    g_motionConfig.maxSpeed = 100;
    g_motionConfig.turnCompensation = 1.0f;
    g_motionConfig.pwmPerSpeed = 2.55f;
}

void loadMotionConfigFromStorage() {
    // Future: read from EEPROM or SD card
    loadDefaultMotionConfig();
}

void saveMotionConfigToStorage() {
    // Future: write to EEPROM or SD card
}

} // namespace RobotAPI