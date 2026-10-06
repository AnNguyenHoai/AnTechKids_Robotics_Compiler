#include "LocalHealthDisplayController.h"

#include "LocalHealthDisplayFormatter.h"

void LocalHealthDisplayController::begin(uint32_t nowMs) {
    _displayAvailable = _display.begin();
    _hasUpdated = false;
    _lastUpdateMs = nowMs;
}

void LocalHealthDisplayController::update(uint32_t nowMs) {
    if (!_displayAvailable) {
        return;
    }

    if (_hasUpdated && (nowMs - _lastUpdateMs) < UPDATE_INTERVAL_MS) {
        return;
    }

    _lastUpdateMs = nowMs;
    _hasUpdated = true;

    const RobotHealth& health = _health.refresh();
    const LocalHealthTextFrame text = LocalHealthDisplayFormatter::format(health);

    LocalHealthDisplayFrame frame;
    frame.line1 = text.lines[0].c_str();
    frame.line2 = text.lines[1].c_str();
    frame.line3 = text.lines[2].c_str();
    frame.line4 = text.lines[3].c_str();

    ++_renderAttempts;
    if (!_display.render(frame)) {
        ++_renderFailures;
        // Optional peripheral: disable repeated display I/O after a runtime
        // rendering failure. Robot execution continues normally.
        _displayAvailable = false;
    }
}
