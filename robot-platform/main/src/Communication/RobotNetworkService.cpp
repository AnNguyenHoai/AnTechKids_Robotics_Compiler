#include "RobotNetworkService.h"

#include <ArduinoOTA.h>
#include <WebServer.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <string.h>

#include "RobotIdentity.h"
#include "RobotDiscoveryService.h"
#include "../Logger/BootLogger.h"

#ifndef ROBOT_WIFI_SSID
#define ROBOT_WIFI_SSID ""
#endif
#ifndef ROBOT_WIFI_PASSWORD
#define ROBOT_WIFI_PASSWORD ""
#endif
#ifndef ROBOT_OTA_PASSWORD
#define ROBOT_OTA_PASSWORD "robot-ota"
#endif

namespace {
WebServer g_server(80);
bool g_ready = false;

void sendHealth() {
    String body = "{\"status\":\"ok\",\"ready\":" + String(g_ready ? "true" : "false") +
                  ",\"hostname\":\"" + String(RobotIdentity::hostname()) +
                  "\",\"ip\":\"" + WiFi.localIP().toString() + "\"}";
    g_server.send(200, "application/json", body);
}

void sendInfo() {
    g_server.send(200, "application/json", RobotIdentity::infoJson(true, g_ready));
}

void onOtaStart() {
    BootLogger::log("OTA", "Firmware update started");
}

void onOtaEnd() {
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
    BootLogger::logFormat("OTA", "Error %u", static_cast<unsigned int>(error));
}

void connectWiFi() {
    if (strlen(ROBOT_WIFI_SSID) == 0) {
        BootLogger::log("NET", "Wi-Fi not configured; OTA disabled");
        return;
    }

    WiFi.mode(WIFI_STA);
    WiFi.setHostname(RobotIdentity::hostname());
    WiFi.begin(ROBOT_WIFI_SSID, ROBOT_WIFI_PASSWORD);

    const uint32_t deadline = millis() + 10000UL;
    while (WiFi.status() != WL_CONNECTED && millis() < deadline) {
        delay(250);
    }

    if (WiFi.status() != WL_CONNECTED) {
        BootLogger::log("NET", "Wi-Fi connection failed; OTA disabled");
        return;
    }

    BootLogger::logFormat("NET", "Wi-Fi connected: %s", WiFi.localIP().toString().c_str());
    MDNS.begin(RobotIdentity::hostname());
    ArduinoOTA.setHostname(RobotIdentity::hostname());
    if (strlen(ROBOT_OTA_PASSWORD) != 0) {
        ArduinoOTA.setPassword(ROBOT_OTA_PASSWORD);
    }
    ArduinoOTA.onStart(onOtaStart);
    ArduinoOTA.onEnd(onOtaEnd);
    ArduinoOTA.onProgress(onOtaProgress);
    ArduinoOTA.onError(onOtaError);
    ArduinoOTA.begin();

    g_server.on("/api/v1/health", HTTP_GET, sendHealth);
    g_server.on("/api/v1/info", HTTP_GET, sendInfo);
    g_server.onNotFound([]() { g_server.send(404, "application/json", "{\"error\":\"not_found\"}"); });
    g_server.begin();
    g_ready = true;

    RobotDiscoveryService::begin();
    BootLogger::logFormat("NET", "Discovery ready on UDP %u", 4210U);
    BootLogger::logFormat("NET", "OTA ready at %s.local", RobotIdentity::hostname());
}
}

namespace RobotNetworkService {
void begin() {
    g_ready = false;
    connectWiFi();
}

void update() {
    if (!g_ready) {
        return;
    }
    ArduinoOTA.handle();
    g_server.handleClient();
    RobotDiscoveryService::update(g_ready, g_ready);
}

bool isReady() { return g_ready; }
const char* hostname() { return RobotIdentity::hostname(); }
}
