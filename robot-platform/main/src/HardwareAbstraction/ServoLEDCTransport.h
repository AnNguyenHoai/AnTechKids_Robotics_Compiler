#pragma once

#include "IServoPwmTransport.h"

class ServoLEDCTransport : public IServoPwmTransport {
public:
    bool attach(uint8_t pin, uint32_t frequencyHz, uint8_t resolutionBits) override;
    bool write(uint8_t pin, uint32_t duty) override;
};
