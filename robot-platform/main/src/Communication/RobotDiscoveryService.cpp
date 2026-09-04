#include "RobotDiscoveryService.h"

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#include "RobotIdentity.h"

namespace {
constexpr uint16_t kDiscoveryPort = 4210;
constexpr char kDiscoveryRequest[] = "ANTECHKIDS_ROBOT_DISCOVER_V1";
constexpr char kDiscoveryResponse[] = "ANTECHKIDS_ROBOT_INFO_V1";

WiFiUDP g_udp;
bool g_ready = false;

void sendResponse(const IPAddress& address, uint16_t port, bool robotReady, bool otaReady) {
    String payload = RobotIdentity::infoJson(robotReady, otaReady);
    g_udp.beginPacket(address, port);
    g_udp.print(kDiscoveryResponse);
    g_udp.print('\n');
    g_udp.print(payload);
    g_udp.endPacket();
}
}

namespace RobotDiscoveryService {

bool begin() {
    g_ready = false;
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    g_ready = g_udp.begin(kDiscoveryPort);
    return g_ready;
}

void update(bool robotReady, bool otaReady) {
    if (!g_ready) {
        return;
    }

    int packetSize = g_udp.parsePacket();
    while (packetSize > 0) {
        char request[64] = {0};
        int bytesRead = g_udp.read(request, sizeof(request) - 1);
        if (bytesRead > 0) {
            request[bytesRead] = '\0';
            String normalized = String(request);
            normalized.trim();
            if (normalized == kDiscoveryRequest) {
                sendResponse(g_udp.remoteIP(), g_udp.remotePort(), robotReady, otaReady);
            }
        }
        packetSize = g_udp.parsePacket();
    }
}

bool isReady() {
    return g_ready;
}

}
