#pragma once

#include <stdint.h>

#include "ILocalHealthDisplay.h"
#include "RobotHealthService.h"

class LocalHealthDisplayController {
public:
    static constexpr uint32_t UPDATE_INTERVAL_MS = 500;

    LocalHealthDisplayController(
        RobotHealthService& health,
        ILocalHealthDisplay& display
    ) : _health(health), _display(display) {}

    void begin(uint32_t nowMs);
    void update(uint32_t nowMs);

    bool displayAvailable() const { return _displayAvailable; }
    uint32_t renderAttempts() const { return _renderAttempts; }
    uint32_t renderFailures() const { return _renderFailures; }

private:
    RobotHealthService& _health;
    ILocalHealthDisplay& _display;

    bool _displayAvailable = false;
    bool _hasUpdated = false;
    uint32_t _lastUpdateMs = 0;
    uint32_t _renderAttempts = 0;
    uint32_t _renderFailures = 0;
};
