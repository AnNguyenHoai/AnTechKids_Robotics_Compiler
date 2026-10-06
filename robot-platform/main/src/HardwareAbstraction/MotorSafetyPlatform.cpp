#include "MotorSafetyPlatform.h"

#include "../../../include/generated/generated_device_config.h"
#include "MotorSafetyGpioGate.h"

MotorSafetyController& systemMotorSafety() {
    static MotorSafetyGpioGate gate;
    static MotorSafetyController controller(
        gate,
        ROBOT_FEATURE_MOTOR != 0
    );
    return controller;
}
