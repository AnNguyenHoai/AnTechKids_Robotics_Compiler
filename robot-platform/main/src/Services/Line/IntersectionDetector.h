#ifndef INTERSECTION_DETECTOR_H
#define INTERSECTION_DETECTOR_H

#include <stdint.h>

/**
 * IntersectionDetector uses a sliding window of recent masks
 * to detect intersections with hysteresis and noise resistance.
 * It triggers when a pattern of mostly '111' occurs with some transitions.
 */
class IntersectionDetector {
public:
    IntersectionDetector();

    bool update(uint8_t mask);
    void reset();

private:
    static constexpr int HISTORY_LEN = 6;  // enough for persistence
    uint8_t _history[HISTORY_LEN];
    int _index;
    int _count;

    // Count how many masks in history are exactly 0b111
    int countAllOnes() const;
};

#endif