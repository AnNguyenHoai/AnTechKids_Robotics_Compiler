#include "StartArmGpioInput.h"

#include "../HAL/GPIOHal.h"
#include "BoardProfile.h"

void StartArmGpioInput::begin() {
    HAL::getGPIO().pinMode(
        BoardProfile::Pins::START_ARM,
        HAL::PinMode::INPUT_PULLUP_MODE
    );
}

bool StartArmGpioInput::isPressed() {
    return HAL::getGPIO().digitalRead(BoardProfile::Pins::START_ARM) ==
           HAL::PinState::LOW_STATE;
}
