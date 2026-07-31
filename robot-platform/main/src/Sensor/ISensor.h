#ifndef SENSOR_ISENSOR_H
#define SENSOR_ISENSOR_H

#include <Arduino.h>

/**
 * Abstract base interface for all sensors.
 * 
 * All sensor drivers must inherit from this class and implement
 * the lifecycle methods. This ensures uniform management by SensorManager.
 */
class ISensor {
public:
    virtual ~ISensor() = default;

    /**
     * Initialize sensor hardware (GPIO, I2C, SPI, etc.).
     * @return true if initialization succeeded.
     */
    virtual bool initialize() = 0;

    /**
     * Update sensor reading (poll hardware). Called periodically.
     */
    virtual void update() = 0;

    /**
     * Return sensor health status.
     * @return true if sensor is functioning normally.
     */
    virtual bool healthy() const = 0;

    /**
     * Return human‑readable sensor name (used for identification).
     */
    virtual const char* name() const = 0;

    /**
     * Read the latest raw value from sensor.
     * @return raw integer value (interpretation depends on sensor type).
     */
    virtual int read() = 0;
};

#endif // SENSOR_ISENSOR_H