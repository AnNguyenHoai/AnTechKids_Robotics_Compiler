#ifndef PLATFORM_ARDUINO_ARDUINOGPIO_H
#define PLATFORM_ARDUINO_ARDUINOGPIO_H

#include "../../HAL/GPIOHal.h"
#include <Arduino.h>

namespace HAL {

class ArduinoGPIO : public GPIOHal {
public:
    ArduinoGPIO() = default;
    ~ArduinoGPIO() = default;

    void pinMode(uint32_t pin, PinMode mode) override;
    void digitalWrite(uint32_t pin, PinState state) override;
    PinState digitalRead(uint32_t pin) override;
    int analogRead(uint32_t pin) override;
    void analogWrite(uint32_t pin, int value) override;
};

} // namespace HAL

#endif