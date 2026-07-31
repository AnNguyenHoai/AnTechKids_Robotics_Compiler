#ifndef SENSOR_SENSORMANAGER_H
#define SENSOR_SENSORMANAGER_H

#include <array>
#include "ISensor.h"
#include "SensorID.h"

/**
 * Singleton manager for all sensors.
 * 
 * Uses SensorID enum for fast, type‑safe lookup.
 * Manages full lifecycle: register, initialize, update, shutdown.
 */
class SensorManager {
public:
    static SensorManager& instance();

    // --- Registration ---
    void registerSensor(SensorID id, ISensor* sensor);

    // --- Lifecycle ---
    bool initializeAll();
    void updateAll();
    void shutdownAll();

    // --- Query ---
    ISensor* getSensor(SensorID id) const;

    // --- Diagnostics ---
    void diagnostics() const;

private:
    SensorManager() = default;
    ~SensorManager() = default;
    SensorManager(const SensorManager&) = delete;
    SensorManager& operator=(const SensorManager&) = delete;

    // Array of sensors, indexed by SensorID
    std::array<ISensor*, static_cast<size_t>(SensorID::Count)> _sensors = {};
};

#endif // SENSOR_SENSORMANAGER_H