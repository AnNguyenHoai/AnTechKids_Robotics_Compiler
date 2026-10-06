#pragma once

#include <array>
#include <string>

#include "RobotHealth.h"

struct LocalHealthTextFrame {
    std::array<std::string, 4> lines;
};

class LocalHealthDisplayFormatter {
public:
    static LocalHealthTextFrame format(const RobotHealth& health);
};
