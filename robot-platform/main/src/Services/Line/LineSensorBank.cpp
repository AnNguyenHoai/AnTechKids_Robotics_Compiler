#include "LineSensorBank.h"
#include "../../HardwareAbstraction/BoardProfile.h"
#include "LineSensorLayout.h"

bool LineSensorBank::begin() {
    _initialized = false;
    _healthy = false;
    _lastMask = 0;

    if (!_mcp.begin()) return false;

    const uint8_t pins[] = {
        BoardProfile::MCP23017::PortA::LINE_FAR_LEFT,
        BoardProfile::MCP23017::PortA::LINE_LEFT,
        BoardProfile::MCP23017::PortA::LINE_CENTER,
        BoardProfile::MCP23017::PortA::LINE_RIGHT,
        BoardProfile::MCP23017::PortA::LINE_FAR_RIGHT,
    };
    for (uint8_t pin : pins) {
        if (!_mcp.configureInput(MCP23017Port::A, pin, false)) return false;
    }

    _initialized = true;
    _healthy = true;
    return true;
}

bool LineSensorBank::readMask(uint8_t& canonicalMask) {
    if (!_initialized) {
        canonicalMask = 0;
        _healthy = false;
        return false;
    }

    uint8_t physical = 0;
    if (!_mcp.readPortA(physical)) {
        canonicalMask = 0;
        _healthy = false;
        return false;
    }

    _lastMask = physicalToCanonical(physical);
    canonicalMask = _lastMask;
    _healthy = true;
    return true;
}

bool LineSensorBank::channel(int channel, bool& detected) const {
    uint8_t bit = 0;
    switch (channel) {
        case 0: bit = LineSensorLayout::MASK_LEFT; break;
        case 1: bit = LineSensorLayout::MASK_CENTER; break;
        case 2: bit = LineSensorLayout::MASK_RIGHT; break;
        case 3: bit = LineSensorLayout::MASK_FAR_LEFT; break;
        case 4: bit = LineSensorLayout::MASK_FAR_RIGHT; break;
        default: detected = false; return false;
    }
    detected = (_lastMask & bit) != 0;
    return true;
}

uint8_t LineSensorBank::physicalToCanonical(uint8_t portA) {
    uint8_t mask = 0;
    if (portA & (1u << BoardProfile::MCP23017::PortA::LINE_FAR_LEFT))  mask |= LineSensorLayout::MASK_FAR_LEFT;
    if (portA & (1u << BoardProfile::MCP23017::PortA::LINE_LEFT))      mask |= LineSensorLayout::MASK_LEFT;
    if (portA & (1u << BoardProfile::MCP23017::PortA::LINE_CENTER))    mask |= LineSensorLayout::MASK_CENTER;
    if (portA & (1u << BoardProfile::MCP23017::PortA::LINE_RIGHT))     mask |= LineSensorLayout::MASK_RIGHT;
    if (portA & (1u << BoardProfile::MCP23017::PortA::LINE_FAR_RIGHT)) mask |= LineSensorLayout::MASK_FAR_RIGHT;
    return LineSensorLayout::sanitizeMask(mask);
}
