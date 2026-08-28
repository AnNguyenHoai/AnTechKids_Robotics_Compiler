#ifndef SENSOR_ENCODER_H
#define SENSOR_ENCODER_H

#include "ISensor.h"
#include <stdint.h>

/**
 * Incremental quadrature encoder driver.
 *
 * H24-C scope:
 * - GPIO/interrupt based A/B decoding
 * - signed pulse count and direction
 * - sampled speed in counts/sec and RPM
 * - no wheel PID and no closed-loop motor control
 */
class Encoder : public ISensor {
public:
    Encoder(int pinA, int pinB, const char* sensorName,
            float countsPerRevolution = 1.0f, bool invertDirection = false);
    ~Encoder() override = default;

    bool initialize() override;
    void update() override;
    bool healthy() const override;
    const char* name() const override;
    void shutdown() override;

    int64_t getCount() const;
    void resetCount(int64_t value = 0);
    int direction() const;

    float getCountsPerSecond() const;
    float getRPM() const;
    float getCountsPerRevolution() const;
    void setCountsPerRevolution(float value);

    int pinA() const;
    int pinB() const;

private:
    static void IRAM_ATTR _handleInterruptA(void* context);
    static void IRAM_ATTR _handleInterruptB(void* context);
    void IRAM_ATTR _handleEdge();
    void _snapshot(int64_t& count, uint32_t& lastEdgeMicros) const;

    int _pinA;
    int _pinB;
    const char* _name;
    float _countsPerRevolution;
    bool _invertDirection;

    volatile int64_t _count;
    volatile int _lastState;
    volatile uint32_t _lastEdgeMicros;
    volatile bool _initialized;

    int64_t _lastSampleCount;
    uint32_t _lastSampleMicros;
    float _countsPerSecond;
    bool _healthy;
};

#endif // SENSOR_ENCODER_H
