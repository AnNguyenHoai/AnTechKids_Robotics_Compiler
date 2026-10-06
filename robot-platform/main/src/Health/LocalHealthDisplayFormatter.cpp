#include "LocalHealthDisplayFormatter.h"

#include <cstdio>

#include "BatteryMonitor.h"
#include "ResetReasonService.h"
#include "RobotHealthService.h"

namespace {

std::string batteryLine(const RobotHealth& health) {
    char buffer[48];
    std::snprintf(
        buffer,
        sizeof(buffer),
        "BAT %s %.2fV",
        BatteryMonitor::stateName(health.battery.state),
        static_cast<double>(health.battery.voltage)
    );
    return buffer;
}

bool isCurrentFault(const RobotHealth& health) {
    return health.motor.state == MotorSafetyState::FAULT ||
           health.battery.state == BatteryState::CRITICAL;
}

} // namespace

LocalHealthTextFrame LocalHealthDisplayFormatter::format(const RobotHealth& health) {
    LocalHealthTextFrame frame;

    if (isCurrentFault(health)) {
        frame.lines[0] = "FAULT";
        frame.lines[1] = std::string("RESET ") +
                         ResetReasonService::nameOf(health.system.resetReason);
        frame.lines[2] = batteryLine(health);
        frame.lines[3] = std::string("MOTOR ") +
                         (health.motor.enabled ? "ENABLED" : "LOCKED");
        return frame;
    }

    frame.lines[0] = "ANTECH ROBOT";
    frame.lines[1] = batteryLine(health);
    frame.lines[2] = health.network.connected ? "WiFi OK" : "WiFi OFF";
    frame.lines[3] = std::string("MOTOR ") +
                     RobotHealthService::motorStateName(health.motor.state);
    return frame;
}
