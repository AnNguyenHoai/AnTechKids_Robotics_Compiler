#pragma once

#include <stdint.h>

#include "BatteryMonitor.h"
#include "ResetReasonService.h"
#include "../HardwareAbstraction/MotorSafetyController.h"

struct RobotHealthSystem {
    uint32_t uptimeMs = 0;
    ResetReason resetReason = ResetReason::UNKNOWN;
    const char* firmwareVersion = "unknown";
    const char* boardProfile = "unknown";
    const char* boardRevision = "unknown";
};

struct RobotHealthBattery {
    float voltage = 0.0f;
    BatteryState state = BatteryState::INVALID;
};

struct RobotHealthMotor {
    bool armed = false;
    bool enabled = false;
    MotorSafetyState state = MotorSafetyState::BOOT;
    MotorDisarmReason lastStopReason = MotorDisarmReason::RESET;
};

struct RobotHealthStart {
    bool pressed = false;
    bool readyForPress = false;
    bool armedByStartThisBoot = false;
};

struct RobotHealthLine {
    bool available = false;
    bool healthy = false;
    uint8_t mask = 0;
};

struct RobotHealthEncoder {
    bool available = false;
    bool healthy = false;
};

struct RobotHealthI2C {
    bool healthy = false;
    bool mcp23017 = false;
};

struct RobotHealthNetwork {
    bool connected = false;
    const char* ip = "";
    int32_t rssi = 0;
};

struct RobotHealth {
    RobotHealthSystem system;
    RobotHealthBattery battery;
    RobotHealthMotor motor;
    RobotHealthStart start;
    RobotHealthLine line;
    RobotHealthEncoder encoder;
    RobotHealthI2C i2c;
    RobotHealthNetwork network;
};
