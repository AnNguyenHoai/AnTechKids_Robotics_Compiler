#include "RobotDiscoveryService.h"

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#include "RobotIdentity.h"

namespace {
constexpr uint16_t kDiscoveryPort = 4210;
constexpr uint32_t kRetryIntervalMs = 2000UL;
constexpr size_t kMaxRequestSize = 64;
constexpr char kDiscoveryRequest[] = "ANTECHKIDS_ROBOT_DISCOVER_V1";
constexpr char kDiscoveryResponse[] = "ANTECHKIDS_ROBOT_INFO_V1";

WiFiUDP g_udp;
bool g_ready = false;
uint32_t g_lastBindAttemptMs = 0;

bool bindSocket() {
    g_lastBindAttemptMs = millis();
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    if (g_ready) {
        return true;
    }

    g_ready = g_udp.begin(kDiscoveryPort);
    return g_ready;
}

void resetSocket() {
    if (g_ready) {
        g_udp.stop();
    }
    g_ready = false;
}

void sendResponse(const IPAddress& address, uint16_t port, bool robotReady, bool networkReady, bool otaReady) {
    String payload = RobotIdentity::infoJson(robotReady, networkReady, otaReady);
    g_udp.beginPacket(address, port);
    g_udp.print(kDiscoveryResponse);
    g_udp.print('\n');
    g_udp.print(payload);
    g_udp.endPacket();
}
}

namespace RobotDiscoveryService {

bool begin() {
    resetSocket();
    return bindSocket();
}

void update(bool robotReady, bool networkReady, bool otaReady) {
    if (WiFi.status() != WL_CONNECTED) {
        resetSocket();
        return;
    }

    if (!g_ready) {
        if (millis() - g_lastBindAttemptMs >= kRetryIntervalMs) {
            bindSocket();
        }
        return;
    }

    // Process at most one datagram per firmware cycle. Draining an arbitrary
    // UDP queue in a while-loop made discovery traffic an unbounded source of
    // line-sensor sample jitter.
    const int packetSize = g_udp.parsePacket();
    if (packetSize <= 0) {
        return;
    }

    if (packetSize >= static_cast<int>(kMaxRequestSize)) {
        while (g_udp.available()) {
            g_udp.read();
        }
        return;
    }

    char request[kMaxRequestSize] = {0};
    const int bytesRead = g_udp.read(request, sizeof(request) - 1);
    if (bytesRead <= 0) {
        return;
    }

    request[bytesRead] = '\0';
    String normalized = String(request);
    normalized.trim();
    if (normalized == kDiscoveryRequest) {
        sendResponse(g_udp.remoteIP(), g_udp.remotePort(), robotReady, networkReady, otaReady);
    }
}

bool isReady() {
    return g_ready;
}

}
