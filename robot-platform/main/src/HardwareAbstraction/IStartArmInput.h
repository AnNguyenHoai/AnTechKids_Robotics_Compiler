#pragma once

class IStartArmInput {
public:
    virtual ~IStartArmInput() = default;
    virtual void begin() = 0;
    virtual bool isPressed() = 0;
};
