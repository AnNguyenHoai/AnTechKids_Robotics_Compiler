#include "StartArmPlatform.h"

#include "MotorSafetyPlatform.h"
#include "StartArmGpioInput.h"

StartArmController& systemStartArm() {
    static StartArmGpioInput input;
    static StartArmController controller(input, systemMotorSafety());
    return controller;
}
