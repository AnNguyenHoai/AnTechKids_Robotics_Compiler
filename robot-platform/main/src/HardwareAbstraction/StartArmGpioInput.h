#pragma once

#include "IStartArmInput.h"

class StartArmGpioInput : public IStartArmInput {
public:
    void begin() override;
    bool isPressed() override;
};
