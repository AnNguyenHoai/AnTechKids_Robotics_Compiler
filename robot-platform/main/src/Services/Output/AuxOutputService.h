#pragma once

#include <stdint.h>

#include "../../HardwareAbstraction/MCP23017Driver.h"

enum class AuxOutputError : uint8_t {
    OK = 0,
    MCP_UNAVAILABLE,
    INVALID_LED_PORT,
    WRITE_ERROR
};

/**
 * V2-SW-008 — logical LED/buzzer output abstraction over MCP23017 Port B.
 *
 * RobotAPI owns public compatibility semantics. This service owns only
 * auxiliary-output pin claiming and MCP-backed writes.
 */
class AuxOutputService {
public:
    explicit AuxOutputService(MCP23017Driver& mcp) : _mcp(mcp) {}

    bool setLed(int publicPort, bool on);
    bool setBuzzer(bool on);

    bool healthy() const {
        return _lastError == AuxOutputError::OK && _mcp.healthy();
    }
    AuxOutputError lastError() const { return _lastError; }

    static bool ledPinForPublicPort(int publicPort, uint8_t& pin);

private:
    bool ensureLedPin(uint8_t pin);
    bool ensureBuzzerPin();
    bool initializeOutputLow(uint8_t pin, bool& initialized);
    void setError(AuxOutputError error) { _lastError = error; }

    MCP23017Driver& _mcp;
    bool _ledLeftInitialized = false;
    bool _ledRightInitialized = false;
    bool _buzzerInitialized = false;
    AuxOutputError _lastError = AuxOutputError::OK;
};
