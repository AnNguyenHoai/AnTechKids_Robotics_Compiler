#include "SensorManager.h"
#include <Arduino.h>

SensorManager& SensorManager::instance() {
    static SensorManager manager;
    return manager;
}

void SensorManager::registerSensor(ISensor* sensor) {
    if (sensor) {
        sensors.push_back(sensor);
    }
}

bool SensorManager::initializeAll() {
    bool allOk = true;
    for (auto s : sensors) {
        if (!s->initialize()) {
            Serial.printf("[SensorManager] Failed to initialize %s\n", s->name());
            allOk = false;
        }
    }
    return allOk;
}

void SensorManager::updateAll() {
    for (auto s : sensors) {
        s->update();
    }
}

void SensorManager::diagnostics() const {
    Serial.println("[SensorManager] Diagnostics:");
    for (auto s : sensors) {
        Serial.printf("  %s: %s\n", s->name(), s->healthy() ? "OK" : "FAIL");
    }
}

ISensor* SensorManager::getSensor(const char* name) const {
    for (auto s : sensors) {
        if (strcmp(s->name(), name) == 0) {
            return s;
        }
    }
    return nullptr;
}

size_t SensorManager::count() const {
    return sensors.size();
}