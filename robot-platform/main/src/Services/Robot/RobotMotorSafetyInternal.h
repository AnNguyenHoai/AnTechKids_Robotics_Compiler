#pragma once

#include "../../HardwareAbstraction/MotorSafetyController.h"

namespace RobotMotorSafetyInternal {

// System-only boundary: clear motor PWM/state first, then disable TB6612 STBY.
// This header is not part of RobotAPI/VM/student surfaces.
void disarm(MotorDisarmReason reason);

} // namespace RobotMotorSafetyInternal
