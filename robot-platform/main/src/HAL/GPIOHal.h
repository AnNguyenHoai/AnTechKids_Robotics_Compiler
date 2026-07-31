#ifndef HAL_GPIOHAL_H
#define HAL_GPIOHAL_H

#include <stdint.h>

namespace HAL {

enum class PinMode : uint8_t {
    INPUT_MODE,             // was INPUT
    OUTPUT_MODE,            // was OUTPUT
    INPUT_PULLUP_MODE,      // was INPUT_PULLUP
    INPUT_PULLDOWN_MODE,    // was INPUT_PULLDOWN
    OUTPUT_OPEN_DRAIN_MODE, // was OUTPUT_OPEN_DRAIN
};

enum class PinState : uint8_t {
    LOW_STATE = 0,   // was LOW
    HIGH_STATE = 1,  // was HIGH
};

class GPIOHal {
public:
    virtual ~GPIOHal() = default;
    virtual void pinMode(uint32_t pin, PinMode mode) = 0;
    virtual void digitalWrite(uint32_t pin, PinState state) = 0;
    virtual PinState digitalRead(uint32_t pin) = 0;
    virtual int analogRead(uint32_t pin) = 0;
    virtual void analogWrite(uint32_t pin, int value) = 0;
};

GPIOHal& getGPIO();

} // namespace HAL

#endif