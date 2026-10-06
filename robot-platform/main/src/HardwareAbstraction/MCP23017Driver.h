#pragma once

#include <stdint.h>

#include "BoardProfile.h"
#include "IMCP23017Transport.h"

enum class MCP23017Error : uint8_t {
    OK = 0,
    NOT_FOUND,
    I2C_ERROR
};

enum class MCP23017Port : uint8_t {
    A = 0,
    B = 1
};

/**
 * V2-SW-003 — MCP23017 register-level HAL.
 *
 * The driver owns MCP register semantics only. It never initializes the System
 * I2C bus directly and has no dependency on motor safety or student APIs.
 */
class MCP23017Driver {
public:
    explicit MCP23017Driver(
        IMCP23017Transport& transport,
        uint8_t address = BoardProfile::MCP23017::ADDRESS
    );

    bool begin();

    bool configureInput(MCP23017Port port, uint8_t pin, bool pullup = false);
    bool configureOutput(MCP23017Port port, uint8_t pin);

    bool readPortA(uint8_t& value);
    bool readPortB(uint8_t& value);
    bool readPin(MCP23017Port port, uint8_t pin, bool& value);

    bool writePin(MCP23017Port port, uint8_t pin, bool value);

    bool healthy() const { return _healthy && _lastError == MCP23017Error::OK; }
    MCP23017Error lastError() const { return _lastError; }
    uint8_t address() const { return _address; }

private:
    static bool validPin(uint8_t pin) { return pin < 8; }

    bool readRegister(uint8_t reg, uint8_t& value);
    bool writeRegister(uint8_t reg, uint8_t value);
    bool updateRegisterBit(uint8_t reg, uint8_t pin, bool set);

    static uint8_t iodirRegister(MCP23017Port port);
    static uint8_t gppuRegister(MCP23017Port port);
    static uint8_t gpioRegister(MCP23017Port port);
    static uint8_t olatRegister(MCP23017Port port);

    void setError(MCP23017Error error);

    IMCP23017Transport& _transport;
    uint8_t _address;
    bool _begun = false;
    bool _healthy = false;
    MCP23017Error _lastError = MCP23017Error::I2C_ERROR;
};
