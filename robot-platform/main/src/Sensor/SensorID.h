#ifndef SENSOR_SENSORID_H
#define SENSOR_SENSORID_H

#include <stdint.h>

/**
 * Unique identifiers for all sensors in the system.
 * 
 * Using enum class provides compile‑time safety and fast array lookups.
 * Add new sensors here when expanding the framework.
 */
enum class SensorID : uint8_t {
    // TCRT5000 line sensors
    LineLeft,
    LineCenter,
    LineRight,
    Ultrasonic,

    // Future sensors (placeholder)
    Touch0,
    Touch1,
    Light,
    Color,
    EncoderLeft,
    EncoderRight,
    IMU,

    // Sentinel
    Count
};

#endif // SENSOR_SENSORID_H