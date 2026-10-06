#pragma once

class IBatterySafetyActions {
public:
    virtual ~IBatterySafetyActions() = default;
    virtual void disarmForCriticalBattery() = 0;
    virtual bool recoverLowBatteryFaultToSafe() = 0;
};
