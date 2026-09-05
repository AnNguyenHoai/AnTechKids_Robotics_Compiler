#include "RobotWiFiConfig.h"

#include <Preferences.h>

#ifndef ROBOT_WIFI_SSID
#define ROBOT_WIFI_SSID ""
#endif
#ifndef ROBOT_WIFI_PASSWORD
#define ROBOT_WIFI_PASSWORD ""
#endif
#ifndef ROBOT_OTA_PASSWORD
#define ROBOT_OTA_PASSWORD ""
#endif

namespace {
constexpr const char* kNamespace = "robot-net";
constexpr const char* kProvisionedKey = "provisioned";
constexpr const char* kSsidKey = "ssid";
constexpr const char* kPasswordKey = "password";
constexpr const char* kOtaPasswordKey = "ota_password";

Preferences g_preferences;
String g_ssid;
String g_password;
String g_otaPassword;
bool g_initialized = false;
bool g_provisioned = false;

bool hasBootstrap() {
    return strlen(ROBOT_WIFI_SSID) > 0;
}

bool loadStored() {
    if (!g_preferences.getBool(kProvisionedKey, false)) {
        return false;
    }
    g_ssid = g_preferences.getString(kSsidKey, "");
    g_password = g_preferences.getString(kPasswordKey, "");
    g_otaPassword = g_preferences.getString(kOtaPasswordKey, "");
    if (g_ssid.length() == 0) {
        return false;
    }
    g_provisioned = true;
    return true;
}
}

namespace RobotWiFiConfig {

bool begin() {
    if (g_initialized) {
        return isConfigured();
    }

    if (!g_preferences.begin(kNamespace, false)) {
        return false;
    }

    g_initialized = true;
    if (loadStored()) {
        Serial.println("[NET] Loaded persistent Wi-Fi configuration from NVS");
        return true;
    }

    if (!hasBootstrap()) {
        Serial.println("[NET] No Wi-Fi bootstrap configuration provisioned");
        return false;
    }

    g_ssid = ROBOT_WIFI_SSID;
    g_password = ROBOT_WIFI_PASSWORD;
    g_otaPassword = ROBOT_OTA_PASSWORD;
    if (!save(g_ssid.c_str(), g_password.c_str(), g_otaPassword.c_str())) {
        Serial.println("[NET] Failed to persist first-flash Wi-Fi configuration");
        return false;
    }
    Serial.println("[NET] First-flash Wi-Fi configuration persisted to NVS");
    return true;
}

bool isConfigured() {
    return g_initialized && g_ssid.length() > 0;
}

bool isProvisioned() {
    return g_initialized && g_provisioned;
}

const char* ssid() { return g_ssid.c_str(); }
const char* password() { return g_password.c_str(); }
const char* otaPassword() { return g_otaPassword.c_str(); }

bool save(const char* newSsid, const char* newPassword, const char* newOtaPassword) {
    if (!newSsid || !newPassword || !newOtaPassword || strlen(newSsid) == 0) {
        return false;
    }
    if (!g_initialized) {
        return false;
    }

    // Write all values first and mark provisioned last so a partial write
    // cannot be mistaken for a valid configuration on the next boot.
    if (g_preferences.putString(kSsidKey, newSsid) == 0 && strlen(newSsid) > 0) {
        return false;
    }
    g_preferences.putString(kPasswordKey, newPassword);
    g_preferences.putString(kOtaPasswordKey, newOtaPassword);
    if (!g_preferences.putBool(kProvisionedKey, true)) {
        return false;
    }

    g_ssid = newSsid;
    g_password = newPassword;
    g_otaPassword = newOtaPassword;
    g_provisioned = true;
    return true;
}

bool clear() {
    if (!g_initialized) {
        return false;
    }
    const bool ok = g_preferences.clear();
    g_ssid = "";
    g_password = "";
    g_otaPassword = "";
    g_provisioned = false;
    return ok;
}

}
