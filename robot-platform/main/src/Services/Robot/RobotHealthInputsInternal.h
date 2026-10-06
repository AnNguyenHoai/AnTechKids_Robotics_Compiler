#pragma once

#include <stdint.h>

namespace RobotHealthInputsInternal {

bool lineAvailable();
bool lineHealthy();
uint8_t lineMask();

bool encoderAvailable();
bool encoderHealthy();

} // namespace RobotHealthInputsInternal
