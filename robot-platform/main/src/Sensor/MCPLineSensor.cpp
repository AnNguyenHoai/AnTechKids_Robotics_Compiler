#include "MCPLineSensor.h"

bool MCPLineSensor::initialize() {
    update();
    return healthy();
}

void MCPLineSensor::update() {
    uint8_t mask = 0;
    bool detected = false;
    if (!_bank.readMask(mask) || !_bank.channel(_channel, detected)) {
        _lastReading = 0;
        _healthy = false;
        return;
    }
    _lastReading = detected ? HIGH : LOW;
    _healthy = _bank.healthy();
}

bool MCPLineSensor::healthy() const {
    return _healthy && _bank.healthy();
}

const char* MCPLineSensor::name() const {
    return _sensorName;
}
