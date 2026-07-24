#include "SensorConfig.h"

SensorConfig g_sensorConfig;

void loadDefaultSensorConfig() {
    g_sensorConfig.ultrasonicTimeoutMs = 30;
    g_sensorConfig.touchDebounceMs = 50;
    g_sensorConfig.lightGain = 1.0f;
    g_sensorConfig.lightOffset = 0;
    g_sensorConfig.lineInverted = false;
    g_sensorConfig.colorOffset = 0;
}

void loadSensorConfigFromStorage() {
    loadDefaultSensorConfig(); // placeholder
}

void saveSensorConfigToStorage() {
    // placeholder
}