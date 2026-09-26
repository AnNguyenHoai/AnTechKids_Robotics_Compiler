#pragma once

#include <stdint.h>

namespace RobotNetworkService {

// Initializes Wi-Fi, HTTP, mDNS, OTA and LAN discovery services.
void begin(bool robotReady = false);

// Services network work cooperatively. budgetUs is a soft inter-call ceiling:
// zero disables the ceiling (used only while OTA already owns the robot), while
// a positive value prevents one firmware cycle from chaining multiple network
// services after the budget has been consumed. Individual Arduino/WiFi library
// calls remain indivisible and are measured by whole-cycle telemetry.
void update(uint32_t budgetUs = 500);

// Network readiness is true only while the robot has an active Wi-Fi service.
bool isReady();

// OTA readiness is separate from network readiness because OTA requires an explicit credential.
bool isOtaReady();

// Robot hardware/runtime readiness is reported independently of network readiness.
void setRobotReady(bool value);

// Exposed for OTA/deployment coordination; does not affect motor or VM execution.
void setUpdateInProgress(bool value);
bool isUpdateInProgress();

const char* hostname();
}
