#include "RobotNetworkService.h"

#include <ArduinoOTA.h>
#include <Update.h>
#include <WebServer.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <string.h>

#include "RobotIdentity.h"
#include "RobotDiscoveryService.h"
#include "RobotWiFiConfig.h"
#include "../Logger/BootLogger.h"
#include "../Services/Robot/RobotAPI.h"

namespace {
constexpr uint32_t kWifiRetryIntervalMs = 5000UL;
constexpr uint32_t kWifiConnectTimeoutMs = 10000UL;
constexpr char kHttpOtaUser[] = "robot";
constexpr char kHttpOtaPath[] = "/api/v1/ota";
constexpr uint8_t kBackgroundServiceSlotCount = 3;

#ifndef ROBOT_OTA_PASSWORD
#define ROBOT_OTA_PASSWORD ""
#endif

enum class WifiState {
    Idle,
    Connecting,
    Connected,
    RetryWait,
};

enum class BackgroundServiceSlot : uint8_t {
    ArduinoOta = 0,
    Http = 1,
    Discovery = 2,
};

WebServer g_server(80);
bool g_networkReady = false;
bool g_otaReady = false;
bool g_robotReady = false;
bool g_updateInProgress = false;
bool g_httpOtaAuthenticated = false;
bool g_httpOtaStarted = false;
bool g_httpOtaCompleted = false;
bool g_handlersRegistered = false;
WifiState g_wifiState = WifiState::Idle;
uint32_t g_wifiStateSinceMs = 0;
uint32_t g_lastWifiAttemptMs = 0;
uint8_t g_nextBackgroundServiceSlot = 0;

bool serviceBudgetExpired(uint32_t startedUs, uint32_t budgetUs) {
    return budgetUs != 0 && static_cast<uint32_t>(micros() - startedUs) >= budgetUs;
}

void sendHealth() {
    const bool aggregateReady = g_robotReady && g_networkReady;
    String body = "{\"status\":\"ok\",\"ready\":" + String(aggregateReady ? "true" : "false") +
                  ",\"robot_ready\":" + String(g_robotReady ? "true" : "false") +
                  ",\"network_ready\":" + String(g_networkReady ? "true" : "false") +
                  ",\"ota\":" + String(g_otaReady ? "true" : "false") +
                  ",\"http_ota\":true\n" +
                  ",\"hostname\":\"" + String(RobotIdentity::hostname()) +
                  "\",\"ip\":\"" + WiFi.localIP().toString() + "\"}";
    g_server.send(200, "application/json", body);
}

void sendInfo() {
    g_server.send(200, "application/json", RobotIdentity::infoJson(g_robotReady, g_networkReady, g_otaReady));
}

void onOtaStart() {
    RobotAPI::Stop();
    RobotNetworkService::setUpdateInProgress(true);
    g_otaReady = false;
    BootLogger::log("OTA", "ArduinoOTA firmware update started");
}

void onOtaEnd() {
    RobotNetworkService::setUpdateInProgress(false);
    g_otaReady = strlen(RobotWiFiConfig::otaPassword()) != 0;
    BootLogger::log("OTA", "ArduinoOTA firmware update complete; rebooting");
}

void onOtaProgress(unsigned int progress, unsigned int total) {
    static unsigned int last = 0;
    const unsigned int percent = total == 0 ? 0 : (progress * 100U) / total;
    if (percent >= last + 10U || percent == 100U) {
        last = percent;
        BootLogger::logFormat("OTA", "ArduinoOTA progress %u%%", percent);
    }
}

void onOtaError(ota_error_t error) {
    RobotNetworkService::setUpdateInProgress(false);
    g_otaReady = strlen(RobotWiFiConfig::otaPassword()) != 0;
    BootLogger::logFormat("OTA", "ArduinoOTA error %u", static_cast<unsigned>(error));
}

void handleHttpOtaUpload() {
    HTTPUpload& upload = g_server.upload();

    if (upload.status == UPLOAD_FILE_START) {
        g_httpOtaAuthenticated = g_server.authenticate(kHttpOtaUser, RobotWiFiConfig::otaPassword());
        g_httpOtaStarted = false;
        g_httpOtaCompleted = false;

        if (!g_httpOtaAuthenticated) {
            BootLogger::log("OTA", "HTTP OTA authentication failed");
            return;
        }

        g_updateInProgress = true;
        RobotAPI::Stop();
        BootLogger::logFormat("OTA", "HTTP OTA started: %s", upload.filename.c_str());

        if (!Update.begin(UPDATE_SIZE_UNKNOWN, U_FLASH)) {
            Update.printError(Serial);
            g_httpOtaAuthenticated = false;
            g_updateInProgress = false;
            return;
        }
        g_httpOtaStarted = true;
        return;
    }

    if (!g_httpOtaAuthenticated || !g_httpOtaStarted) {
        return;
    }

    if (upload.status == UPLOAD_FILE_WRITE) {
        const size_t written = Update.write(upload.buf, upload.currentSize);
        if (written != upload.currentSize) {
            Update.printError(Serial);
            g_httpOtaStarted = false;
            g_updateInProgress = false;
        }
    } else if (upload.status == UPLOAD_FILE_END) {
        if (Update.end(true)) {
            g_httpOtaCompleted = true;
            BootLogger::logFormat("OTA", "HTTP OTA upload complete: %lu bytes", static_cast<unsigned long>(upload.totalSize));
        } else {
            Update.printError(Serial);
            g_httpOtaStarted = false;
            g_updateInProgress = false;
        }
    } else if (upload.status == UPLOAD_FILE_ABORTED) {
        Update.end(false);
        g_httpOtaStarted = false;
        g_updateInProgress = false;
        BootLogger::log("OTA", "HTTP OTA upload aborted");
    }
}

void handleHttpOtaFinish() {
    if (!g_httpOtaAuthenticated) {
        g_server.requestAuthentication(BASIC_AUTH, "Robot OTA");
        return;
    }

    g_server.sendHeader("Connection", "close");
    if (!g_httpOtaStarted || !g_httpOtaCompleted || Update.hasError()) {
        g_updateInProgress = false;
        g_server.send(500, "text/plain", Update.hasError() ? Update.errorString() : "OTA upload failed");
        g_httpOtaAuthenticated = false;
        return;
    }

    g_server.send(200, "text/plain", "OK - firmware received, rebooting");
    g_httpOtaAuthenticated = false;
    g_updateInProgress = false;
    delay(250);
    ESP.restart();
}

void registerHttpHandlers() {
    if (g_handlersRegistered) {
        return;
    }

    g_server.on("/api/v1/health", HTTP_GET, sendHealth);
    g_server.on("/api/v1/info", HTTP_GET, sendInfo);
    g_server.on(kHttpOtaPath, HTTP_POST, handleHttpOtaFinish, handleHttpOtaUpload);
    g_server.onNotFound([]() {
        g_server.send(404, "application/json", "{\"error\":\"not_found\"}");
    });
    g_handlersRegistered = true;
}

bool startWifiConnection() {
    if (!RobotWiFiConfig::isConfigured()) {
        g_networkReady = false;
        g_otaReady = false;
        g_wifiState = WifiState::Idle;
        BootLogger::log("NET", "Wi-Fi not configured; OTA disabled");
        return false;
    }

    WiFi.disconnect(false, false);
    WiFi.mode(WIFI_STA);
    WiFi.setHostname(RobotIdentity::hostname());
    WiFi.begin(RobotWiFiConfig::ssid(), RobotWiFiConfig::password());

    g_networkReady = false;
    g_otaReady = false;
    g_wifiState = WifiState::Connecting;
    g_wifiStateSinceMs = millis();
    g_lastWifiAttemptMs = g_wifiStateSinceMs;
    BootLogger::log("NET", "Wi-Fi connection attempt started");
    return true;
}

void onWifiConnected() {
    g_wifiState = WifiState::Connected;
    g_networkReady = true;
    BootLogger::logFormat("NET", "Wi-Fi connected: %s", WiFi.localIP().toString().c_str());

    MDNS.end();
    MDNS.begin(RobotIdentity::hostname());

    ArduinoOTA.setHostname(RobotIdentity::hostname());
    if (strlen(RobotWiFiConfig::otaPassword()) != 0) {
        ArduinoOTA.setPassword(RobotWiFiConfig::otaPassword());
        g_otaReady = true;
        ArduinoOTA.onStart(onOtaStart);
        ArduinoOTA.onEnd(onOtaEnd);
        ArduinoOTA.onProgress(onOtaProgress);
        ArduinoOTA.onError(onOtaError);
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
}

void handleWifiState() {
    const wl_status_t status = WiFi.status();

    if (g_wifiState == WifiState::Connecting) {
        if (status == WL_CONNECTED) {
            onWifiConnected();
            return;
        }
        if (millis() - g_wifiStateSinceMs >= kWifiConnectTimeoutMs) {
            WiFi.disconnect(false, false);
            g_networkReady = false;
            g_otaReady = false;
            g_wifiState = WifiState::RetryWait;
            g_wifiStateSinceMs = millis();
            BootLogger::log("NET", "Wi-Fi connection failed; will retry");
        }
        return;
    }

    if (g_wifiState == WifiState::RetryWait) {
        if (status == WL_CONNECTED) {
            onWifiConnected();
            return;
        }
        if (millis() - g_wifiStateSinceMs >= kWifiRetryIntervalMs) {
            startWifiConnection();
        }
        return;
    }

    if (g_wifiState == WifiState::Connected && status != WL_CONNECTED) {
        g_networkReady = false;
        g_otaReady = false;
        RobotDiscoveryService::begin();
        g_wifiState = WifiState::RetryWait;
        g_wifiStateSinceMs = millis();
        BootLogger::log("NET", "Wi-Fi disconnected; network services unavailable");
    }
}

bool serviceBackgroundSlot(uint8_t slot) {
    switch (static_cast<BackgroundServiceSlot>(slot)) {
        case BackgroundServiceSlot::ArduinoOta:
            if (!g_otaReady) {
                return false;
            }
            ArduinoOTA.handle();
            return true;
        case BackgroundServiceSlot::Http:
            g_server.handleClient();
            return true;
        case BackgroundServiceSlot::Discovery:
            RobotDiscoveryService::update(g_robotReady, g_networkReady, g_otaReady);
            return true;
    }
    return false;
}

void serviceBackgroundRoundRobin(uint32_t startedUs, uint32_t budgetUs) {
    const uint8_t startSlot = g_nextBackgroundServiceSlot;

    for (uint8_t offset = 0; offset < kBackgroundServiceSlotCount; ++offset) {
        const uint8_t slot = static_cast<uint8_t>((startSlot + offset) % kBackgroundServiceSlotCount);
        if (!serviceBackgroundSlot(slot)) {
            continue;
        }

        // Advance ownership immediately after the indivisible call. If this
        // call consumes the remaining budget, the next firmware cycle starts
        // with the next eligible service instead of restarting from OTA.
        g_nextBackgroundServiceSlot = static_cast<uint8_t>((slot + 1U) % kBackgroundServiceSlotCount);

        if (g_updateInProgress || serviceBudgetExpired(startedUs, budgetUs)) {
            return;
        }
    }
}

}

namespace RobotNetworkService {

void begin(bool robotReady) {
    g_networkReady = false;
    g_otaReady = false;
    g_robotReady = robotReady;
    g_updateInProgress = false;
    g_httpOtaAuthenticated = false;
    g_httpOtaStarted = false;
    g_httpOtaCompleted = false;
    g_wifiState = WifiState::Idle;
    g_wifiStateSinceMs = millis();
    g_lastWifiAttemptMs = 0;
    g_nextBackgroundServiceSlot = 0;

    if (!RobotWiFiConfig::begin()) {
        BootLogger::log("NET", "No Wi-Fi configuration available");
    }
    startWifiConnection();
}

void update(uint32_t budgetUs) {
    const uint32_t startedUs = micros();
    handleWifiState();
    if (!g_networkReady) {
        return;
    }

    // Once an OTA transaction has started, main() has already stopped motors
    // and suspended VM work. Keep pumping both OTA transports until completion;
    // budgetUs is intentionally passed as zero from that OTA-owned path.
    if (g_updateInProgress) {
        ArduinoOTA.handle();
        g_server.handleClient();
        return;
    }

    if (serviceBudgetExpired(startedUs, budgetUs)) {
        return;
    }

    // Normal operation is cooperatively bounded but must also be fair. A
    // fixed OTA -> HTTP -> discovery order allowed an over-budget early call
    // to starve later services forever during sustained VM execution.
    serviceBackgroundRoundRobin(startedUs, budgetUs);
}

bool isReady() { return g_networkReady; }
bool isOtaReady() { return g_otaReady; }
void setRobotReady(bool value) { g_robotReady = value; }
void setUpdateInProgress(bool value) { g_updateInProgress = value; }
bool isUpdateInProgress() { return g_updateInProgress; }
const char* hostname() { return RobotIdentity::hostname(); }

}
