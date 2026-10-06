#pragma once

#include "IMCP23017Transport.h"

/**
 * Production MCP23017 transport over the shared V2 System I2C bus.
 * This class performs transactions only; SystemI2CBusManager owns bus init.
 */
class MCP23017WireTransport : public IMCP23017Transport {
public:
    bool ensureBusInitialized() override;
    bool probe(uint8_t address) override;
    bool writeRegister(uint8_t address, uint8_t reg, uint8_t value) override;
    bool readRegister(uint8_t address, uint8_t reg, uint8_t& value) override;
};
