#pragma once

#include <stdint.h>

class IServoPwmTransport {
public:
    virtual ~IServoPwmTransport() = default;
    virtual bool attach(uint8_t pin, uint32_t frequencyHz, uint8_t resolutionBits) = 0;
    virtual bool write(uint8_t pin, uint32_t duty) = 0;
};
