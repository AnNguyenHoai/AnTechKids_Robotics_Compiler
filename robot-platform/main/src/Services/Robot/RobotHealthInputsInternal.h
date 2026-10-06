#pragma once

#include <stdint.h>

namespace RobotHealthInputsInternal {

bool lineAvailable();
bool lineHealthy();
uint8_t lineMask();

bool encoderAvailable();
bool encoderHealthy();
int64_t encoderLeftCount();
int64_t encoderRightCount();

} // namespace RobotHealthInputsInternal
