#ifndef SENSOR_TCRT5000_H
#define SENSOR_TCRT5000_H

#include "DigitalSensor.h"

/**
 * TCRT5000 infrared line sensor driver.
 * 
 * Implements DigitalSensor and adds semantic methods for line detection.
 * Supports configurable threshold (if analog version is used, but here digital).
 */
class TCRT5000 : public DigitalSensor {
public:
    /**
     * Constructor.
     * @param pin        GPIO pin connected to sensor output.
     * @param sensorName Unique name (e.g., "line_left").
     * @param threshold  Threshold value (default HIGH = 1 for digital).
     */
    TCRT5000(int pin, const char* sensorName, int threshold = HIGH);

    virtual ~TCRT5000() = default;

    // --- ISensor interface ---
    bool initialize() override;
    void update() override;
    bool healthy() const override;
    const char* name() const override;
    void shutdown() override;

    // --- DigitalSensor interface ---
    int read() const override;

    // --- Semantic API ---
    bool isLineDetected() const;
    int rawLevel() const;

    // Shared-snapshot owner bypasses update() to perform exactly one physical
    // read per channel for the current control cycle.
    void SampleHardwareDirect();
    void ApplySnapshotReading(int reading);

    // Qualification fixed-rate producer must not mutate the legacy cached
    // reading from another task. This performs one GPIO read and evaluates the
    // configured threshold without changing _lastReading.
    bool ReadHardwareDetectedDirect() const;

    // --- Calibration support ---
    void setThreshold(int threshold);
    int getThreshold() const;

private:
    int _pin;
    const char* _name;
    int _threshold;
    int _lastReading;
    bool _healthy;
};

#endif // SENSOR_TCRT5000_H
