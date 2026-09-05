#!/usr/bin/env python3
"""Generate a self-contained Arduino IDE sketch for robot first flash.

The generated sketch is a small network/OTA bootstrap loader. RoboStudio writes
credentials into a local header, the teacher opens the generated sketch in
Arduino IDE and uploads it over USB. Once the robot joins the classroom Wi-Fi,
RoboStudio can discover it and OTA-flash the normal robot firmware.

Generated credentials live under .robostudio/ and must never be committed.
"""
from __future__ import annotations

import argparse
from pathlib import Path


SKETCH_TEMPLATE = r'''#include <Arduino.h>
#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <WebServer.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#include "bootstrap_secrets.h"

namespace {
constexpr uint16_t DISCOVERY_PORT = 4210;
constexpr char DISCOVERY_REQUEST[] = "ANTECHKIDS_ROBOT_DISCOVER_V1";
constexpr char DISCOVERY_RESPONSE[] = "ANTECHKIDS_ROBOT_INFO_V1";
constexpr char HOSTNAME_PREFIX[] = "robot-";

WebServer server(80);
WiFiUDP udp;
String deviceId;
String hostname;
String displayName;

String boolJson(bool value) {
    return value ? "true" : "false";
}

void initIdentity() {
    uint64_t mac = ESP.getEfuseMac();
    char id[13] = {0};
    snprintf(id, sizeof(id), "%012llX", mac);
    deviceId = String("robot-") + id;
    hostname = String(HOSTNAME_PREFIX) + String(id + 6);
    displayName = String("AnTechKids Robot ") + String(id + 6);
}

String infoJson() {
    return String("{\"protocol\":\"antechkids.robot.v1\",\"schema_version\":1") +
           ",\"device_id\":\"" + deviceId +
           "\",\"name\":\"" + displayName +
           "\",\"hostname\":\"" + hostname +
           "\",\"ip\":\"" + WiFi.localIP().toString() +
           "\",\"target\":\"esp32\"" +
           ",\"firmware\":\"first-flash-bootstrap\"" +
           ",\"robot_ready\":true" +
           ",\"network_ready\":true" +
           ",\"ready\":true" +
           ",\"ota\":true" +
           ",\"capabilities\":{\"motor\":false,\"encoder\":false,\"line_sensor\":false,\"ultrasonic\":false,\"imu\":false,\"servo\":false,\"buzzer\":false}}";
}

void sendInfo() {
    server.send(200, "application/json", infoJson());
}

void handleDiscovery() {
    int packetSize = udp.parsePacket();
    while (packetSize > 0) {
        char request[64] = {0};
        int count = udp.read(request, sizeof(request) - 1);
        if (count > 0) {
            request[count] = '\0';
            String normalized(request);
            normalized.trim();
            if (normalized == DISCOVERY_REQUEST) {
                udp.beginPacket(udp.remoteIP(), udp.remotePort());
                udp.print(DISCOVERY_RESPONSE);
                udp.print('\n');
                udp.print(infoJson());
                udp.endPacket();
            }
        }
        packetSize = udp.parsePacket();
    }
}

void connectWifi() {
    WiFi.mode(WIFI_STA);
    WiFi.setHostname(hostname.c_str());
    WiFi.begin(ROBOT_WIFI_SSID, ROBOT_WIFI_PASSWORD);

    Serial.print("[BOOTSTRAP] Connecting to Wi-Fi");
    const unsigned long deadline = millis() + 20000UL;
    while (WiFi.status() != WL_CONNECTED && millis() < deadline) {
        delay(250);
        Serial.print('.');
    }
    Serial.println();

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[BOOTSTRAP] Wi-Fi connection failed. Reboot and check the generated config.");
        return;
    }

    MDNS.begin(hostname.c_str());
    ArduinoOTA.setHostname(hostname.c_str());
    ArduinoOTA.setPassword(ROBOT_OTA_PASSWORD);
    ArduinoOTA.onStart([]() { Serial.println("[OTA] Update started"); });
    ArduinoOTA.onEnd([]() { Serial.println("[OTA] Update complete"); });
    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        Serial.printf("[OTA] %u%%\n", total ? (progress * 100U) / total : 0U);
    });
    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("[OTA] Error %u\n", static_cast<unsigned int>(error));
    });
    ArduinoOTA.begin();

    server.on("/api/v1/health", HTTP_GET, []() {
        server.send(200, "application/json",
                    "{\"status\":\"ok\",\"ready\":true,\"robot_ready\":true,\"network_ready\":true,\"ota\":true}");
    });
    server.on("/api/v1/info", HTTP_GET, sendInfo);
    server.onNotFound([]() {
        server.send(404, "application/json", "{\"error\":\"not_found\"}");
    });
    server.begin();
    udp.begin(DISCOVERY_PORT);

    Serial.println("[BOOTSTRAP] READY");
    Serial.printf("[BOOTSTRAP] Robot: %s\n", displayName.c_str());
    Serial.printf("[BOOTSTRAP] IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[BOOTSTRAP] OTA: %s.local\n", hostname.c_str());
}
}

void setup() {
    Serial.begin(115200);
    delay(300);
    initIdentity();
    Serial.println("[BOOTSTRAP] AnTechKids first-flash firmware");
    connectWifi();
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        ArduinoOTA.handle();
        server.handleClient();
        handleDiscovery();
    } else {
        delay(250);
    }
}
'''


def _cpp_string(value: str) -> str:
    # Generated header is C++ source. Escape backslashes, quotes and control chars.
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def generate_package(ssid: str, wifi_password: str, ota_password: str, output: Path) -> Path:
    ssid = ssid.strip()
    if not ssid:
        raise ValueError("Wi-Fi SSID is required.")
    if len(ssid.encode("utf-8")) > 32:
        raise ValueError("Wi-Fi SSID must be at most 32 UTF-8 bytes.")
    if len(wifi_password.encode("utf-8")) > 63:
        raise ValueError("Wi-Fi password must be at most 63 UTF-8 bytes.")
    if not ota_password:
        raise ValueError("OTA password is required for first-flash bootstrap.")
    if len(ota_password.encode("utf-8")) > 63:
        raise ValueError("OTA password must be at most 63 UTF-8 bytes.")

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "FirstFlash.ino").write_text(SKETCH_TEMPLATE, encoding="utf-8")
    (output / "bootstrap_secrets.h").write_text(
        "#pragma once\n\n"
        "#define ROBOT_WIFI_SSID \"" + _cpp_string(ssid) + "\"\n"
        "#define ROBOT_WIFI_PASSWORD \"" + _cpp_string(wifi_password) + "\"\n"
        "#define ROBOT_OTA_PASSWORD \"" + _cpp_string(ota_password) + "\"\n",
        encoding="utf-8",
    )
    (output / "README.txt").write_text(
        "AnTechKids Robot — First Flash via Arduino IDE\n\n"
        "1. Open FirstFlash.ino in Arduino IDE.\n"
        "2. Select ESP32 Dev Module (ESP32 DevKit).\n"
        "3. Select the robot USB port.\n"
        "4. Click Upload.\n"
        "5. After the robot joins Wi-Fi, use RoboStudio > Discover Robots.\n"
        "6. Use RoboStudio OTA to replace this bootstrap firmware with the normal robot firmware.\n\n"
        "This folder is generated locally by RoboStudio. Do not commit it.\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Arduino IDE first-flash bootstrap sketch")
    parser.add_argument("--ssid", required=True)
    parser.add_argument("--password", default="")
    parser.add_argument("--ota-password", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        path = generate_package(args.ssid, args.password, args.ota_password, args.output)
    except ValueError as exc:
        print(f"ARDUINO FIRST-FLASH ERROR: {exc}")
        return 2
    print(f"ARDUINO FIRST-FLASH PACKAGE READY: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
