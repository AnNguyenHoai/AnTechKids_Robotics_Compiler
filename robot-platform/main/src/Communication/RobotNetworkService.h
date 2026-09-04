#pragma once

namespace RobotNetworkService {

// Initializes Wi-Fi, HTTP, mDNS, OTA and LAN discovery services.
void begin(bool robotReady = false);
void update();

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
