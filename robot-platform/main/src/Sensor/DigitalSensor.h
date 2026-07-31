#ifndef SENSOR_DIGITALSENSOR_H
#define SENSOR_DIGITALSENSOR_H

#include "ISensor.h"

/**
 * Base class for digital sensors (output is 0 or 1).
 * 
 * Provides a `read()` method that returns the current digital level.
 * Subclasses should implement semantic methods (e.g., isPressed()).
 */
class DigitalSensor : public ISensor {
public:
    virtual ~DigitalSensor() = default;

    /**
     * Read the current digital value (0 or 1).
     * This is a low‑level method; prefer semantic methods in subclasses.
     */
    virtual int read() const = 0;
};

#endif // SENSOR_DIGITALSENSOR_H