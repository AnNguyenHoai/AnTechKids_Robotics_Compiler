#pragma once
#include <stdint.h>

struct SensorConfig {
    // Ultrasonic
    uint32_t ultrasonicTimeoutMs = 30;

    // Touch (debounce)
    uint32_t touchDebounceMs = 50;

    // Light
    float lightGain = 1.0f;
    int lightOffset = 0;

    // Line
    bool lineInverted = false;

    // Color
    int colorOffset = 0;
};

extern SensorConfig g_sensorConfig;

void loadDefaultSensorConfig();
void loadSensorConfigFromStorage();
void saveSensorConfigToStorage();