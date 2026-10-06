#pragma once

class IMotorSafetyGate {
public:
    virtual ~IMotorSafetyGate() = default;
    virtual void beginSafe() = 0;
    virtual void setDriverEnabled(bool enabled) = 0;
};
