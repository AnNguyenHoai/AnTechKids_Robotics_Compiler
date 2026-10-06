#pragma once

#include <stdint.h>

#include "IMotorSafetyGate.h"

enum class MotorSafetyState : uint8_t {
    BOOT = 0,
    SAFE,
    ARMED,
    RUNNING,
    FAULT
};

enum class MotorDisarmReason : uint8_t {
    NONE = 0,
    EXPLICIT_SAFETY_STOP,
    OTA,
    LOW_BATTERY,
    FATAL_PLATFORM_FAULT,
    MOTOR_SAFETY_FAULT,
    WATCHDOG,
    RESET,
    REBOOT
};

class MotorSafetyController {
public:
    MotorSafetyController(IMotorSafetyGate& gate, bool motorFeatureEnabled)
        : _gate(gate), _motorFeatureEnabled(motorFeatureEnabled) {}

    void begin();
    bool arm();
    void disarm(MotorDisarmReason reason);
    bool recoverFaultToSafe(MotorDisarmReason reason);

    bool isArmed() const;
    bool isDriverEnabled() const { return _driverEnabled; }
    MotorSafetyState state() const { return _state; }
    MotorDisarmReason lastDisarmReason() const { return _lastDisarmReason; }

    // Lowest physical output path calls this before submitting PWM.
    // Zero command is always allowed so outputs can be actively cleared.
    bool allowPhysicalOutput(int leftCommand, int rightCommand);

private:
    static bool isFaultReason(MotorDisarmReason reason);

    IMotorSafetyGate& _gate;
    bool _motorFeatureEnabled = false;
    bool _driverEnabled = false;
    MotorSafetyState _state = MotorSafetyState::BOOT;
    MotorDisarmReason _lastDisarmReason = MotorDisarmReason::RESET;
};
