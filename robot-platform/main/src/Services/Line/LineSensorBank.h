#pragma once
#include <stdint.h>
#include "../../HardwareAbstraction/MCP23017Driver.h"

class LineSensorBank {
public:
    explicit LineSensorBank(MCP23017Driver& mcp) : _mcp(mcp) {}

    bool begin();
    bool readMask(uint8_t& canonicalMask);
    bool channel(int channel, bool& detected) const;
    bool healthy() const { return _initialized && _healthy && _mcp.healthy(); }
    uint8_t lastMask() const { return _lastMask; }

    static uint8_t physicalToCanonical(uint8_t portA);

private:
    MCP23017Driver& _mcp;
    bool _initialized = false;
    bool _healthy = false;
    uint8_t _lastMask = 0;
};
