#pragma once

namespace RobotDiscoveryService {

// Initializes the LAN discovery listener. Returns true when the UDP socket is ready.
bool begin();

// Keeps discovery alive across transient Wi-Fi/socket failures.
void update(bool robotReady, bool networkReady, bool otaReady);

bool isReady();

}
