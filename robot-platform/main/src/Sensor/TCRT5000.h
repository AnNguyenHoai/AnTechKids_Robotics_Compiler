#ifndef SENSOR_TCRT5000_H
#define SENSOR_TCRT5000_H

#include "ISensor.h"

/**
 * TCRT5000 infrared line sensor driver.
 * 
 * This class manages a single TCRT5000 channel (one digital pin).
 * It implements ISensor and can be registered with SensorManager.
 */
class TCRT5000 : public ISensor {
public:
    /**
     * Constructor.
     * @param pin        GPIO pin connected to sensor output.
     * @param sensorName Unique name (e.g., "line_left").
     */
    TCRT5000(int pin, const char* sensorName);

    virtual ~TCRT5000() = default;

    // ISensor interface
    bool initialize() override;
    void update() override;
    bool healthy() const override;
    const char* name() const override;
    int read() override;

private:
    int _pin;
    const char* _name;
    int _lastReading;
    bool _healthy;
};

#endif // SENSOR_TCRT5000_H