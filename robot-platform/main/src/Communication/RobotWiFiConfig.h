#pragma once

#include <Arduino.h>

namespace RobotWiFiConfig {

// Loads persistent Wi-Fi/OTA credentials. On first boot, compile-time
// bootstrap credentials are copied into NVS and become the canonical runtime
// configuration.
bool begin();
bool isConfigured();
bool isProvisioned();

const char* ssid();
const char* password();
const char* otaPassword();

// Persist a new configuration atomically from the caller's perspective.
bool save(const char* ssid, const char* password, const char* otaPassword);

// Clear persistent credentials and return to an unprovisioned state.
bool clear();

}
