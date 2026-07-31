#ifndef SENSOR_DISTANCESENSOR_H
#define SENSOR_DISTANCESENSOR_H

#include "ISensor.h"

/**
 * Abstract base for distance measuring sensors.
 * 
 * Adds semantic methods specific to range finding.
 */
class DistanceSensor : public ISensor {
public:
    virtual ~DistanceSensor() = default;

    /**
     * Current distance in the sensor's unit.
     * @return Distance value, or negative value if no object detected.
     */
    virtual float distanceCm() const = 0;

    /**
     * Maximum measurable range.
     * @return Range in centimeters.
     */
    virtual float maxRangeCm() const = 0;

    /**
     * Unit of measurement.
     * @return String like "cm", "mm", "inch".
     */
    virtual const char* unit() const = 0;
};

#endif