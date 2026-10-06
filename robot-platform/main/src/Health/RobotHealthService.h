#pragma once

#include "IRobotHealthSource.h"

class RobotHealthService {
public:
    explicit RobotHealthService(IRobotHealthSource& source) : _source(source) {}

    const RobotHealth& refresh();
    const RobotHealth& current() const { return _health; }

    static const char* motorStateName(MotorSafetyState state);
    static const char* motorStopReasonName(MotorDisarmReason reason);

private:
    IRobotHealthSource& _source;
    RobotHealth _health;
};
