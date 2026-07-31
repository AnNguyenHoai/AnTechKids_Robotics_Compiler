#ifndef SENSOR_SENSORMANAGER_H
#define SENSOR_SENSORMANAGER_H

#include <vector>
#include "ISensor.h"

/**
 * Singleton manager for all sensors.
 * 
 * Responsibilities:
 * - Register sensors
 * - Initialize all sensors
 * - Periodically update all sensors
 * - Provide diagnostics
 * - Query sensors by name
 */
class SensorManager {
public:
    static SensorManager& instance();

    // Registration
    void registerSensor(ISensor* sensor);

    // Lifecycle
    bool initializeAll();
    void updateAll();
    void diagnostics() const;

    // Query
    ISensor* getSensor(const char* name) const;
    size_t count() const;

private:
    SensorManager() = default;
    ~SensorManager() = default;
    SensorManager(const SensorManager&) = delete;
    SensorManager& operator=(const SensorManager&) = delete;

    std::vector<ISensor*> sensors;
};

#endif // SENSOR_SENSORMANAGER_H