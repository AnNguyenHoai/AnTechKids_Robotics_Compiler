#include "MCP23017Driver.h"

namespace {
constexpr uint8_t REG_IODIRA = 0x00;
constexpr uint8_t REG_IODIRB = 0x01;
constexpr uint8_t REG_GPPUA  = 0x0C;
constexpr uint8_t REG_GPPUB  = 0x0D;
constexpr uint8_t REG_GPIOA  = 0x12;
constexpr uint8_t REG_GPIOB  = 0x13;
constexpr uint8_t REG_OLATA  = 0x14;
constexpr uint8_t REG_OLATB  = 0x15;
}

MCP23017Driver::MCP23017Driver(IMCP23017Transport& transport, uint8_t address)
    : _transport(transport), _address(address) {}

bool MCP23017Driver::begin() {
    _healthy = false;
    _lastError = MCP23017Error::I2C_ERROR;

    if (!_transport.ensureBusInitialized()) {
        setError(MCP23017Error::I2C_ERROR);
        return false;
    }

    if (!_transport.probe(_address)) {
        setError(MCP23017Error::NOT_FOUND);
        return false;
    }

    // Fail-safe startup: all MCP pins begin as inputs with pull-ups disabled.
    // Feature tasks explicitly claim pins later (Line5 inputs / LED+buzzer outputs).
    if (!writeRegister(REG_IODIRA, 0xFF) ||
        !writeRegister(REG_IODIRB, 0xFF) ||
        !writeRegister(REG_GPPUA, 0x00) ||
        !writeRegister(REG_GPPUB, 0x00)) {
        return false;
    }

    _healthy = true;
    _lastError = MCP23017Error::OK;
    return true;
}

bool MCP23017Driver::configureInput(MCP23017Port port, uint8_t pin, bool pullup) {
    if (!validPin(pin)) {
        setError(MCP23017Error::I2C_ERROR);
        return false;
    }

    if (!updateRegisterBit(iodirRegister(port), pin, true)) {
        return false;
    }
    return updateRegisterBit(gppuRegister(port), pin, pullup);
}

bool MCP23017Driver::configureOutput(MCP23017Port port, uint8_t pin) {
    if (!validPin(pin)) {
        setError(MCP23017Error::I2C_ERROR);
        return false;
    }

    // Disable pull-up before driving the pin as an output.
    if (!updateRegisterBit(gppuRegister(port), pin, false)) {
        return false;
    }
    return updateRegisterBit(iodirRegister(port), pin, false);
}

bool MCP23017Driver::readPortA(uint8_t& value) {
    return readRegister(REG_GPIOA, value);
}

bool MCP23017Driver::readPortB(uint8_t& value) {
    return readRegister(REG_GPIOB, value);
}

bool MCP23017Driver::readPin(MCP23017Port port, uint8_t pin, bool& value) {
    if (!validPin(pin)) {
        setError(MCP23017Error::I2C_ERROR);
        return false;
    }

    uint8_t portValue = 0;
    if (!readRegister(gpioRegister(port), portValue)) {
        return false;
    }

    value = (portValue & static_cast<uint8_t>(1u << pin)) != 0;
    return true;
}

bool MCP23017Driver::writePin(MCP23017Port port, uint8_t pin, bool value) {
    if (!validPin(pin)) {
        setError(MCP23017Error::I2C_ERROR);
        return false;
    }
    return updateRegisterBit(olatRegister(port), pin, value);
}

bool MCP23017Driver::readRegister(uint8_t reg, uint8_t& value) {
    if (!_transport.readRegister(_address, reg, value)) {
        setError(MCP23017Error::I2C_ERROR);
        return false;
    }
    _lastError = MCP23017Error::OK;
    return true;
}

bool MCP23017Driver::writeRegister(uint8_t reg, uint8_t value) {
    if (!_transport.writeRegister(_address, reg, value)) {
        setError(MCP23017Error::I2C_ERROR);
        return false;
    }
    _lastError = MCP23017Error::OK;
    return true;
}

bool MCP23017Driver::updateRegisterBit(uint8_t reg, uint8_t pin, bool set) {
    uint8_t value = 0;
    if (!readRegister(reg, value)) {
        return false;
    }

    const uint8_t mask = static_cast<uint8_t>(1u << pin);
    const uint8_t updated = set
        ? static_cast<uint8_t>(value | mask)
        : static_cast<uint8_t>(value & static_cast<uint8_t>(~mask));

    if (updated == value) {
        return true;
    }
    return writeRegister(reg, updated);
}

uint8_t MCP23017Driver::iodirRegister(MCP23017Port port) {
    return port == MCP23017Port::A ? REG_IODIRA : REG_IODIRB;
}

uint8_t MCP23017Driver::gppuRegister(MCP23017Port port) {
    return port == MCP23017Port::A ? REG_GPPUA : REG_GPPUB;
}

uint8_t MCP23017Driver::gpioRegister(MCP23017Port port) {
    return port == MCP23017Port::A ? REG_GPIOA : REG_GPIOB;
}

uint8_t MCP23017Driver::olatRegister(MCP23017Port port) {
    return port == MCP23017Port::A ? REG_OLATA : REG_OLATB;
}

void MCP23017Driver::setError(MCP23017Error error) {
    _lastError = error;
    if (error != MCP23017Error::OK) {
        _healthy = false;
    }
}
