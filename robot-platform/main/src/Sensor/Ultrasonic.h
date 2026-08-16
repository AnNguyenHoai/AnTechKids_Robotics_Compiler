#ifndef SENSOR_ULTRASONIC_H
#define SENSOR_ULTRASONIC_H

#include "DistanceSensor.h"

/**
 * HC-SR04 Ultrasonic Distance Sensor Driver.
 * 
 * Implements DistanceSensor with improved health model:
 * - Consecutive timeouts (> 3) mark sensor as unhealthy.
 * - A successful reading resets the timeout counter.
 */
class Ultrasonic : public DistanceSensor {
public:
    Ultrasonic(int trigPin, int echoPin, uint32_t timeoutUs = 30000, const char* name = "ultrasonic");
    ~Ultrasonic() = default;

    // ISensor interface
    bool initialize() override;
    void update() override;
    bool healthy() const override;
    const char* name() const override;
    void shutdown() override;

    // DistanceSensor interface
    float distanceCm() const override;
    float maxRangeCm() const override;
    const char* unit() const override;

    // === Diagnostic getters ===
    uint8_t getConsecutiveTimeouts() const { return _consecutiveTimeouts; }
    float getLastDistance() const { return _lastDistance; }

private:
    int _trigPin;
    int _echoPin;
    uint32_t _timeoutUs;
    const char* _name;
    float _lastDistance;
    bool _healthy;
    bool _initialized;

    static constexpr uint8_t MAX_CONSECUTIVE_TIMEOUTS = 3;
    uint8_t _consecutiveTimeouts;
};

#endif