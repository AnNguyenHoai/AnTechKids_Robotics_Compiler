#ifndef SENSOR_ISENSOR_H
#define SENSOR_ISENSOR_H

#include <Arduino.h>

/**
 * Abstract base interface for all sensors.
 * 
 * This interface defines the minimal lifecycle methods.
 * Concrete sensor categories (Digital, Analog, Distance, etc.)
 * will add their own reading methods.
 */
class ISensor {
public:
    virtual ~ISensor() = default;

    /**
     * Initialize hardware (GPIO, I2C, SPI, etc.).
     * @return true if initialization succeeded.
     */
    virtual bool initialize() = 0;

    /**
     * Poll hardware and update internal state.
     * Called periodically by SensorManager.
     */
    virtual void update() = 0;

    /**
     * Return sensor health status.
     * @return true if sensor is functioning normally.
     */
    virtual bool healthy() const = 0;

    /**
     * Return human‑readable sensor name (for diagnostics).
     */
    virtual const char* name() const = 0;

    /**
     * Shut down sensor (release resources, etc.).
     * Default implementation does nothing.
     */
    virtual void shutdown() {}
};

#endif // SENSOR_ISENSOR_H