#include "MotorSafetyGpioGate.h"

#include "../HAL/GPIOHal.h"
#include "BoardProfile.h"

void MotorSafetyGpioGate::beginSafe() {
    HAL::getGPIO().pinMode(
        BoardProfile::Pins::MOTOR_SAFE_EN,
        HAL::PinMode::OUTPUT_MODE
    );
    HAL::getGPIO().digitalWrite(
        BoardProfile::Pins::MOTOR_SAFE_EN,
        HAL::PinState::LOW_STATE
    );
}

void MotorSafetyGpioGate::setDriverEnabled(bool enabled) {
    HAL::getGPIO().digitalWrite(
        BoardProfile::Pins::MOTOR_SAFE_EN,
        enabled ? HAL::PinState::HIGH_STATE : HAL::PinState::LOW_STATE
    );
}
