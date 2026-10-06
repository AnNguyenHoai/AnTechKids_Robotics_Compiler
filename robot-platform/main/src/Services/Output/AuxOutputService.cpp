#include "AuxOutputService.h"

#include "../../HardwareAbstraction/BoardProfile.h"

bool AuxOutputService::ledPinForPublicPort(int publicPort, uint8_t& pin) {
    // Preserve the V1 Set3CLed parity contract:
    // odd public ports -> logical Right LED, even -> logical Left LED.
    if (publicPort <= 0) {
        pin = 0;
        return false;
    }

    pin = (publicPort % 2 == 0)
        ? BoardProfile::MCP23017::PortB::LED_LEFT
        : BoardProfile::MCP23017::PortB::LED_RIGHT;
    return true;
}

bool AuxOutputService::initializeOutputLow(uint8_t pin, bool& initialized) {
    if (initialized) return true;

    if (!_mcp.begin()) {
        setError(AuxOutputError::MCP_UNAVAILABLE);
        return false;
    }

    // Prime OLAT low before switching direction to output to avoid a startup
    // high pulse on LEDs or the external buzzer driver.
    if (!_mcp.writePin(MCP23017Port::B, pin, false)) {
        setError(AuxOutputError::WRITE_ERROR);
        return false;
    }
    if (!_mcp.configureOutput(MCP23017Port::B, pin)) {
        setError(AuxOutputError::WRITE_ERROR);
        return false;
    }

    initialized = true;
    setError(AuxOutputError::OK);
    return true;
}

bool AuxOutputService::ensureLedPin(uint8_t pin) {
    if (pin == BoardProfile::MCP23017::PortB::LED_LEFT) {
        return initializeOutputLow(pin, _ledLeftInitialized);
    }
    if (pin == BoardProfile::MCP23017::PortB::LED_RIGHT) {
        return initializeOutputLow(pin, _ledRightInitialized);
    }

    setError(AuxOutputError::INVALID_LED_PORT);
    return false;
}

bool AuxOutputService::ensureBuzzerPin() {
    return initializeOutputLow(
        BoardProfile::MCP23017::PortB::BUZZER_CTRL,
        _buzzerInitialized
    );
}

bool AuxOutputService::setLed(int publicPort, bool on) {
    uint8_t pin = 0;
    if (!ledPinForPublicPort(publicPort, pin)) {
        setError(AuxOutputError::INVALID_LED_PORT);
        return false;
    }

    if (!ensureLedPin(pin)) return false;
    if (!_mcp.writePin(MCP23017Port::B, pin, on)) {
        setError(AuxOutputError::WRITE_ERROR);
        return false;
    }

    setError(AuxOutputError::OK);
    return true;
}

bool AuxOutputService::setBuzzer(bool on) {
    if (!ensureBuzzerPin()) return false;
    if (!_mcp.writePin(
            MCP23017Port::B,
            BoardProfile::MCP23017::PortB::BUZZER_CTRL,
            on)) {
        setError(AuxOutputError::WRITE_ERROR);
        return false;
    }

    setError(AuxOutputError::OK);
    return true;
}
