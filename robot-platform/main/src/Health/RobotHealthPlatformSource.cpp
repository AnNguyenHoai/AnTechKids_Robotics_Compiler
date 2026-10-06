#include "RobotHealthPlatformSource.h"

#include <Arduino.h>

#include "BatteryMonitorPlatform.h"
#include "ResetReasonPlatform.h"
#include "../Communication/RobotIdentity.h"
#include "../Communication/RobotNetworkService.h"
#include "../HardwareAbstraction/BoardProfile.h"
#include "../HardwareAbstraction/MCP23017Platform.h"
#include "../HardwareAbstraction/MotorSafetyPlatform.h"
#include "../HardwareAbstraction/StartArmPlatform.h"
#include "../HardwareAbstraction/SystemI2CBusManager.h"
#include "../Services/Robot/RobotHealthInputsInternal.h"

void RobotHealthPlatformSource::populate(RobotHealth& health) {
    health.system.uptimeMs = millis();
    health.system.resetReason = systemResetReasonService().reason();
    health.system.firmwareVersion = RobotIdentity::firmwareVersion();
    health.system.boardProfile = BoardProfile::ID;
    health.system.boardRevision = BoardProfile::REVISION;

    // Read-only health snapshot: do not trigger a fresh ADC sample here.
    health.battery.voltage = systemBatteryMonitor().voltage();
    health.battery.state = systemBatteryMonitor().state();

    auto& motor = systemMotorSafety();
    health.motor.armed = motor.isArmed();
    health.motor.enabled = motor.isDriverEnabled();
    health.motor.state = motor.state();
    health.motor.lastStopReason = motor.lastDisarmReason();

    auto& start = systemStartArm();
    health.start.pressed = start.isPressed();
    health.start.readyForPress = start.isReadyForPress();
    health.start.armedByStartThisBoot = start.armedByStartThisBoot();

    health.line.available = RobotHealthInputsInternal::lineAvailable();
    health.line.healthy = RobotHealthInputsInternal::lineHealthy();
    health.line.mask = RobotHealthInputsInternal::lineMask();

    health.encoder.available = RobotHealthInputsInternal::encoderAvailable();
    health.encoder.healthy = RobotHealthInputsInternal::encoderHealthy();

    health.i2c.healthy = SystemI2CBusManager::instance().initialized();
    health.i2c.mcp23017 = systemMCP23017().healthy();

    health.network.connected = RobotNetworkService::isReady();
    health.network.ip = RobotNetworkService::ipAddress();
    health.network.rssi = RobotNetworkService::rssi();
}
