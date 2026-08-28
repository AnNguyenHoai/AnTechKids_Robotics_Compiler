#pragma once

#include <Arduino.h>
#include <stdint.h>

/**
 * Quadrature encoder driver for ESP32.
 *
 * H24-C/H24-D contract:
 * - count is signed and represents decoded quadrature edges
 * - countsPerRevolution is the decoded count for one wheel revolution
 * - GPIO34/35/36/39 are input-only; external encoder outputs must provide valid levels
 */
class Encoder {
public:
    Encoder(uint8_t pinA, uint8_t pinB, float countsPerRevolution = 1.0f);

    bool begin();
    void update();

    int64_t getCount() const;
    void resetCount(int64_t value = 0);

    float getCountsPerSecond() const;
    float getRPM() const;
    int getDirection() const;

    void setCountsPerRevolution(float value);
    float getCountsPerRevolution() const;

    void setInverted(bool inverted);
    bool isInverted() const;

private:
    static void IRAM_ATTR isrA(void* arg);
    static void IRAM_ATTR isrB(void* arg);
    void IRAM_ATTR handleEdge();

    uint8_t _pinA;
    uint8_t _pinB;
    volatile int64_t _count = 0;
    volatile uint8_t _state = 0;
    volatile bool _inverted = false;

    int64_t _lastSampleCount = 0;
    uint32_t _lastSampleUs = 0;
    float _countsPerSecond = 0.0f;
    float _countsPerRevolution;
    bool _started = false;

    static const int8_t TRANSITION_TABLE[16];
};
