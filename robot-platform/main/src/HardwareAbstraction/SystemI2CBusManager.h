#pragma once

#include <stdint.h>

/**
 * V2-SW-002 — single owner for the AnTech Robot V2 System I2C bus.
 *
 * Physical pins/frequency come from BoardProfile. Peripheral drivers may use
 * Wire transactions after ensureInitialized(), but must never initialize the physical bus.
 */
class SystemI2CBusManager {
public:
    static SystemI2CBusManager& instance();

    // Performs at most one Wire.begin() attempt per boot.
    bool begin();

    // Idempotent convenience entry point for peripheral drivers.
    bool ensureInitialized();

    bool initialized() const { return _initialized; }
    bool beginAttempted() const { return _beginAttempted; }
    uint32_t frequencyHz() const;

private:
    SystemI2CBusManager() = default;

    bool _beginAttempted = false;
    bool _initialized = false;
};
