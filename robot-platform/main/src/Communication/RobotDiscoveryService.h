#pragma once

namespace RobotDiscoveryService {

// Start the LAN discovery responder. Safe to call after Wi-Fi is connected.
bool begin();

// Process discovery requests. Call frequently from the main loop.
void update(bool robotReady, bool otaReady);

bool isReady();

}
