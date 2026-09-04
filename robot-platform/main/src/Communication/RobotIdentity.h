#pragma once

#include <Arduino.h>

namespace RobotIdentity {

constexpr uint8_t kSchemaVersion = 1;

// Stable device identity derived from the ESP32 eFuse MAC address.
const char* deviceId();
const char* hostname();
const char* displayName();
const char* target();
const char* firmwareVersion();

// Returns the current hardware capability set as a compact JSON object.
String capabilitiesJson();

// Returns the complete discovery identity payload.
// `ready` is retained as a compatibility aggregate of robot and network readiness.
String infoJson(bool robotReady, bool networkReady, bool otaReady);

}
