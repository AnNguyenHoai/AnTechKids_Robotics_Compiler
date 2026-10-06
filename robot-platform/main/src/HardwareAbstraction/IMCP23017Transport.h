#pragma once

#include <stdint.h>

/**
 * Injectable byte-register transport used by MCP23017Driver.
 *
 * Production uses MCP23017WireTransport. Unit tests inject a fake transport so
 * the real driver state/error logic can be tested without ESP32 hardware.
 */
class IMCP23017Transport {
public:
    virtual ~IMCP23017Transport() = default;

    virtual bool ensureBusInitialized() = 0;
    virtual bool probe(uint8_t address) = 0;
    virtual bool writeRegister(uint8_t address, uint8_t reg, uint8_t value) = 0;
    virtual bool readRegister(uint8_t address, uint8_t reg, uint8_t& value) = 0;
};
