#include "BatterySafetyPlatform.h"

#include "BatteryMonitorPlatform.h"
#include "../HardwareAbstraction/MotorSafetyPlatform.h"
#include "../Services/Robot/RobotMotorSafetyInternal.h"

namespace {

class RobotBatterySafetyActions : public IBatterySafetyActions {
public:
    void disarmForCriticalBattery() override {
        RobotMotorSafetyInternal::disarm(MotorDisarmReason::LOW_BATTERY);
    }

    bool recoverLowBatteryFaultToSafe() override {
        return systemMotorSafety().recoverFaultToSafe(MotorDisarmReason::LOW_BATTERY);
    }
};

} // namespace

BatterySafetyPolicy& systemBatterySafetyPolicy() {
    static RobotBatterySafetyActions actions;
    static BatterySafetyPolicy policy(systemBatteryMonitor(), actions);
    return policy;
}
