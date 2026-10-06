#pragma once

#include "IMotorSafetyGate.h"

class MotorSafetyGpioGate : public IMotorSafetyGate {
public:
    void beginSafe() override;
    void setDriverEnabled(bool enabled) override;
};
