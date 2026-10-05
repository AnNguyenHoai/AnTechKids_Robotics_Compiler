#ifndef INTERSECTION_DETECTOR_H
#define INTERSECTION_DETECTOR_H

#include <stdint.h>

/**
 * IntersectionDetector uses a sliding window of recent five-bit masks
 * to detect intersections with hysteresis and noise resistance.
 */
class IntersectionDetector {
public:
    IntersectionDetector();

    bool update(uint8_t mask);
    void reset();

private:
    static constexpr int HISTORY_LEN = 6;
    uint8_t _history[HISTORY_LEN];
    int _index;
    int _count;

    int countCandidates() const;
};

#endif