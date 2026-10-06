#pragma once

#include "IRobotHealthSource.h"

class RobotHealthPlatformSource : public IRobotHealthSource {
public:
    void populate(RobotHealth& health) override;
};
