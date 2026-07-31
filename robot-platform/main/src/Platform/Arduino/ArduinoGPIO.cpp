#include "ArduinoGPIO.h"
#include <Arduino.h>

namespace HAL {

void ArduinoGPIO::pinMode(uint32_t pin, PinMode mode) {
    uint8_t arduinoMode;
    switch (mode) {
        case PinMode::INPUT_MODE:             arduinoMode = INPUT; break;
        case PinMode::OUTPUT_MODE:            arduinoMode = OUTPUT; break;
        case PinMode::INPUT_PULLUP_MODE:      arduinoMode = INPUT_PULLUP; break;
        case PinMode::INPUT_PULLDOWN_MODE:    arduinoMode = INPUT_PULLDOWN; break;
        case PinMode::OUTPUT_OPEN_DRAIN_MODE: arduinoMode = OUTPUT; break;
        default:                              arduinoMode = INPUT; break;
    }
    ::pinMode(pin, arduinoMode);
}

void ArduinoGPIO::digitalWrite(uint32_t pin, PinState state) {
    ::digitalWrite(pin, (state == PinState::HIGH_STATE) ? HIGH : LOW);
}

PinState ArduinoGPIO::digitalRead(uint32_t pin) {
    int val = ::digitalRead(pin);
    return (val == HIGH) ? PinState::HIGH_STATE : PinState::LOW_STATE;
}

int ArduinoGPIO::analogRead(uint32_t pin) {
    return ::analogRead(pin);
}

void ArduinoGPIO::analogWrite(uint32_t pin, int value) {
    ::analogWrite(pin, value);
}

GPIOHal& getGPIO() {
    static ArduinoGPIO instance;
    return instance;
}

} // namespace HAL