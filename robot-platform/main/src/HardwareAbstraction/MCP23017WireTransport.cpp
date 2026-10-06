#include "MCP23017WireTransport.h"

#include <Wire.h>

#include "SystemI2CBusManager.h"

bool MCP23017WireTransport::ensureBusInitialized() {
    return SystemI2CBusManager::instance().ensureInitialized();
}

bool MCP23017WireTransport::probe(uint8_t address) {
    Wire.beginTransmission(address);
    return Wire.endTransmission() == 0;
}

bool MCP23017WireTransport::writeRegister(uint8_t address, uint8_t reg, uint8_t value) {
    Wire.beginTransmission(address);
    Wire.write(reg);
    Wire.write(value);
    return Wire.endTransmission() == 0;
}

bool MCP23017WireTransport::readRegister(uint8_t address, uint8_t reg, uint8_t& value) {
    Wire.beginTransmission(address);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) {
        return false;
    }

    const size_t received = Wire.requestFrom(address, static_cast<uint8_t>(1));
    if (received != 1 || !Wire.available()) {
        return false;
    }

    value = static_cast<uint8_t>(Wire.read());
    return true;
}
