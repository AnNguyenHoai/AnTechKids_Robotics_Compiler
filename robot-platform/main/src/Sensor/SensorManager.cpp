#include "SensorManager.h"
#include <Arduino.h>

SensorManager& SensorManager::instance() {
    static SensorManager manager;
    return manager;
}

void SensorManager::registerSensor(SensorID id, ISensor* sensor) {
    size_t index = static_cast<size_t>(id);
    if (index < _sensors.size()) {
        if (_sensors[index] != nullptr) {
            // Overwrite? For safety, warn and delete old.
            // But we assume each ID is registered once.
            Serial.printf("[SensorManager] Warning: overwriting sensor at ID %d\n", index);
            delete _sensors[index];
        }
        _sensors[index] = sensor;
    }
}

bool SensorManager::initializeAll() {
    bool allOk = true;
    for (size_t i = 0; i < _sensors.size(); ++i) {
        auto s = _sensors[i];
        if (s != nullptr) {
            if (!s->initialize()) {
                Serial.printf("[SensorManager] Failed to init %s (ID %d)\n", s->name(), i);
                allOk = false;
            }
        }
    }
    return allOk;
}

void SensorManager::updateAll() {
    for (auto s : _sensors) {
        if (s != nullptr) {
            s->update();
        }
    }
}

void SensorManager::shutdownAll() {
    for (auto s : _sensors) {
        if (s != nullptr) {
            s->shutdown();
            delete s;   // clean up memory
            s = nullptr;
        }
    }
}

ISensor* SensorManager::getSensor(SensorID id) const {
    size_t index = static_cast<size_t>(id);
    if (index < _sensors.size()) {
        return _sensors[index];
    }
    return nullptr;
}

void SensorManager::diagnostics() const {
    Serial.println("[SensorManager] Diagnostics:");
    for (size_t i = 0; i < _sensors.size(); ++i) {
        auto s = _sensors[i];
        if (s != nullptr) {
            Serial.printf("  %s (ID %d): %s\n", s->name(), i,
                          s->healthy() ? "OK" : "FAIL");
        } else {
            Serial.printf("  ID %d: not registered\n", i);
        }
    }
}