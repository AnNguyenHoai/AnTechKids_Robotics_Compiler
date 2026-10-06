#pragma once

#include <stdint.h>

#include "IStartArmInput.h"
#include "MotorSafetyController.h"

class StartArmController {
public:
    static constexpr uint32_t DEBOUNCE_MS = 30;

    StartArmController(IStartArmInput& input, MotorSafetyController& motorSafety)
        : _input(input), _motorSafety(motorSafety) {}

    void begin(uint32_t nowMs);
    void onSystemReady(uint32_t nowMs);

    // Returns true only when this update causes SAFE -> ARMED.
    bool update(uint32_t nowMs);

    bool isPressed() const { return _stablePressed; }
    bool isReadyForPress() const { return _systemReady && !_requireRelease; }
    bool armedByStartThisBoot() const { return _armedByStartThisBoot; }

private:
    IStartArmInput& _input;
    MotorSafetyController& _motorSafety;

    bool _systemReady = false;
    bool _rawPressed = false;
    bool _stablePressed = false;
    bool _requireRelease = true;
    bool _armedByStartThisBoot = false;
    uint32_t _lastRawChangeMs = 0;
};
