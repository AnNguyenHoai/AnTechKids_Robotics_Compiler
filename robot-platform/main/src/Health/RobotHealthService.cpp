#include "RobotHealthService.h"

const RobotHealth& RobotHealthService::refresh() {
    _source.populate(_health);
    return _health;
}

const char* RobotHealthService::motorStateName(MotorSafetyState state) {
    switch (state) {
        case MotorSafetyState::BOOT: return "BOOT";
        case MotorSafetyState::SAFE: return "SAFE";
        case MotorSafetyState::ARMED: return "ARMED";
        case MotorSafetyState::RUNNING: return "RUNNING";
        case MotorSafetyState::FAULT: return "FAULT";
        default: return "UNKNOWN";
    }
}

const char* RobotHealthService::motorStopReasonName(MotorDisarmReason reason) {
    switch (reason) {
        case MotorDisarmReason::NONE: return "NONE";
        case MotorDisarmReason::EXPLICIT_SAFETY_STOP: return "EXPLICIT_SAFETY_STOP";
        case MotorDisarmReason::OTA: return "OTA";
        case MotorDisarmReason::LOW_BATTERY: return "LOW_BATTERY";
        case MotorDisarmReason::FATAL_PLATFORM_FAULT: return "FATAL_PLATFORM_FAULT";
        case MotorDisarmReason::MOTOR_SAFETY_FAULT: return "MOTOR_SAFETY_FAULT";
        case MotorDisarmReason::WATCHDOG: return "WATCHDOG";
        case MotorDisarmReason::RESET: return "RESET";
        case MotorDisarmReason::REBOOT: return "REBOOT";
        default: return "UNKNOWN";
    }
}
