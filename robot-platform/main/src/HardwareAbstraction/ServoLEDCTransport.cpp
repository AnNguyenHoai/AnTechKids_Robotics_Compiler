#include "ServoLEDCTransport.h"

#include <Arduino.h>
#include "../Compatibility/LEDCCompat.h"

bool ServoLEDCTransport::attach(uint8_t pin, uint32_t frequencyHz, uint8_t resolutionBits) {
    ledcAttach(pin, frequencyHz, resolutionBits);
    return true;
}

bool ServoLEDCTransport::write(uint8_t pin, uint32_t duty) {
    ledcWrite(pin, duty);
    return true;
}
