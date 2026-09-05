#include "RobotNetworkService.h"

#include <ArduinoOTA.h>
#include <WebServer.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <string.h>

#include "RobotIdentity.h"
#include "RobotDiscoveryService.h"
#include "RobotWiFiConfig.h"
#include "../Logger/BootLogger.h"

namespace {
constexpr uint32_t kWifiRetryIntervalMs = 5000UL;
constexpr uint32_t kWifiConnectTimeoutMs = 10000UL;

// Keep the legacy compile-time contract as an empty fallback. H27-B0 supplies
// a real credential through wifi_config.py when the bootstrap/OTA build
// environment is used; this fallback never introduces a shared OTA password.
#ifndef ROBOT_OTA_PASSWORD
#define ROBOT_OTA_PASSWORD ""
#endif

WebServer g_server(80);
bool g_networkReady = false;
bool g_otaReady = false;
bool g_robotReady = false;
bool g_updateInProgress = false;
uint32_t g_lastWifiAttemptMs = 0;
bool g_handlersRegistered = false;

void sendHealth() {
    const bool aggregateReady = g_robotReady && g_networkReady;
    String body = "{\"status\":\"ok\",\"ready\":" + String(aggregateReady ? "true" : "false") +
                  ",\"robot_ready\":" + String(g_robotReady ? "true" : "false") +
                  ",\"network_ready\":" + String(g_networkReady ? "true" : "false") +
                  ",\"ota\":" + String(g_otaReady ? "true" : "false") +
                  ",\"hostname\":\"" + String(RobotIdentity::hostname()) +
                  "\",\"ip\":\"" + WiFi.localIP().toString() + "\"}";
    g_server.send(200, "application/json", body);
}

void sendInfo() {
    g_server.send(200, "application/json", RobotIdentity::infoJson(g_robotReady, g_networkReady, g_otaReady));
}

void onOtaStart() {
    RobotNetworkService::setUpdateInProgress(true);
    g_otaReady = false;
    BootLogger::log("OTA", "Firmware update started");
}

void onOtaEnd() {
    RobotNetworkService::setUpdateInProgress(false);
    BootLogger::log("OTA", "Firmware update complete; rebooting");
}

void onOtaProgress(unsigned int progress, unsigned int total) {
    static unsigned int last = 0;
    unsigned int percent = total == 0 ? 0 : (progress * 100U) / total;
    if (percent >= last + 10U || percent == 100U) {
        last = percent;
        BootLogger::logFormat("OTA", "Progress %u%%", percent);
    }
}

void onOtaError(ota_error_t error) {
    RobotNetworkService::setUpdateInProgress(false);
    g_otaReady = strlen(RobotWiFiConfig::otaPassword()) != 0;
    BootLogger::logFormat("OTA", "Error %u", static_cast<unsigned int>(error));
}

void registerHttpHandlers() {
    if (g_handlersRegistered) {
        return;
    }
    g_server.on("/api/v1/health", HTTP_GET, sendHealth);
    g_server.on("/api/v1/info", HTTP_GET, sendInfo);
    g_server.onNotFound([]() {
        g_server.send(404, "application/json", "{\"error\":\"not_found\"}");
    });
    g_handlersRegistered = true;
}

bool connectWiFi() {
    g_lastWifiAttemptMs = millis();
    if (!RobotWiFiConfig::isConfigured()) {
        g_networkReady = false;
        g_otaReady = false;
        BootLogger::log("NET", "Wi-Fi not configured; OTA disabled");
        return false;
    }

    WiFi.mode(WIFI_STA);
    WiFi.setHostname(RobotIdentity::hostname());
    WiFi.begin(RobotWiFiConfig::ssid(), RobotWiFiConfig::password());

    const uint32_t deadline = millis() + kWifiConnectTimeoutMs;
    while (WiFi.status() != WL_CONNECTED && millis() < deadline) {
        delay(250);
    }

    if (WiFi.status() != WL_CONNECTED) {
        g_networkReady = false;
        g_otaReady = false;
        BootLogger::log("NET", "Wi-Fi connection failed; will retry");
        return false;
    }

    g_networkReady = true;
    BootLogger::logFormat("NET", "Wi-Fi connected: %s", WiFi.localIP().toString().c_str());

    MDNS.begin(RobotIdentity::hostname());
    ArduinoOTA.setHostname(RobotIdentity::hostname());
    if (strlen(RobotWiFiConfig::otaPassword()) != 0) {
        ArduinoOTA.setPassword(RobotWiFiConfig::otaPassword());
        g_otaReady = true;
        ArduinoOTA.begin();
        BootLogger::logFormat("NET", "OTA ready at %s.local", RobotIdentity::hostname());
    } else {
        g_otaReady = false;
        BootLogger::log("NET", "OTA disabled: OTA password is not provisioned");
    }

    registerHttpHandlers();
    g_server.begin();

    if (!RobotDiscoveryService::begin()) {
        BootLogger::log("NET", "Discovery bind failed; will retry");
    } else {
        BootLogger::logFormat("NET", "Discovery ready on UDP %u", 4210U);
    }
    return true;
}

void handleNetworkRecovery() {
    if (WiFi.status() == WL_CONNECTED) {
        if (!g_networkReady) {
            connectWiFi();
        }
        return;
    }

    if (g_networkReady) {
        g_networkReady = false;
        g_otaReady = false;
        RobotDiscoveryService::begin();
        BootLogger::log("NET", "Wi-Fi disconnected; network services unavailable");
    }

    if (millis() - g_lastWifiAttemptMs >= kWifiRetryIntervalMs) {
        connectWiFi();
    }
}
}

namespace RobotNetworkService {

void begin(bool robotReady) {
    g_networkReady = false;
    g_otaReady = false;
    g_robotReady = robotReady;
    g_updateInProgress = false;
    g_lastWifiAttemptMs = millis();

    if (!RobotWiFiConfig::begin()) {
        BootLogger::log("NET", "No Wi-Fi configuration available");
    }
    connectWiFi();
}

void update() {
    handleNetworkRecovery();
    if (!g_networkReady) {
        return;
    }

    if (g_otaReady && !g_updateInProgress) {
        ArduinoOTA.handle();
    }
    g_server.handleClient();
    RobotDiscoveryService::update(g_robotReady, g_networkReady, g_otaReady);
}

bool isReady() { return g_networkReady; }
bool isOtaReady() { return g_otaReady; }
void setRobotReady(bool value) { g_robotReady = value; }
void setUpdateInProgress(bool value) { g_updateInProgress = value; }
bool isUpdateInProgress() { return g_updateInProgress; }
const char* hostname() { return RobotIdentity::hostname(); }

}
