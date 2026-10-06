#include "SystemI2CBusManager.h"

#include <Arduino.h>
#include <Wire.h>

#include "BoardProfile.h"

namespace {
constexpr uint16_t SYSTEM_I2C_TIMEOUT_MS = 20;
}

SystemI2CBusManager& SystemI2CBusManager::instance() {
    static SystemI2CBusManager manager;
    return manager;
}

bool SystemI2CBusManager::begin() {
    if (_beginAttempted) {
        return _initialized;
    }

    _beginAttempted = true;

    _initialized = Wire.begin(
        BoardProfile::Pins::SYSTEM_I2C_SDA,
        BoardProfile::Pins::SYSTEM_I2C_SCL,
        BoardProfile::SystemI2C::INITIAL_FREQUENCY_HZ
    );

    if (!_initialized) {
        Serial.println("[SystemI2C] Wire.begin failed; shared bus unavailable.");
        return false;
    }

    // Bound transactions so an absent/misbehaving device cannot stall runtime
    // indefinitely. Device-specific errors are handled by each peripheral.
    Wire.setTimeOut(SYSTEM_I2C_TIMEOUT_MS);

    Serial.printf(
        "[SystemI2C] Ready SDA=%u SCL=%u freq=%luHz timeout=%ums\n",
        static_cast<unsigned>(BoardProfile::Pins::SYSTEM_I2C_SDA),
        static_cast<unsigned>(BoardProfile::Pins::SYSTEM_I2C_SCL),
        static_cast<unsigned long>(BoardProfile::SystemI2C::INITIAL_FREQUENCY_HZ),
        static_cast<unsigned>(SYSTEM_I2C_TIMEOUT_MS)
    );
    return true;
}

bool SystemI2CBusManager::ensureInitialized() {
    return begin();
}

uint32_t SystemI2CBusManager::frequencyHz() const {
    return BoardProfile::SystemI2C::INITIAL_FREQUENCY_HZ;
}
