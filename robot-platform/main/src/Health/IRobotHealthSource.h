#pragma once

#include "RobotHealth.h"

class IRobotHealthSource {
public:
    virtual ~IRobotHealthSource() = default;
    virtual void populate(RobotHealth& health) = 0;
};
