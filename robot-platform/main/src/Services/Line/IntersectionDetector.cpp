#include "IntersectionDetector.h"

IntersectionDetector::IntersectionDetector() : _index(0), _count(0) {
    reset();
}

void IntersectionDetector::reset() {
    for (int i = 0; i < HISTORY_LEN; ++i) _history[i] = 0;
    _index = 0;
    _count = 0;
}

bool IntersectionDetector::update(uint8_t mask) {
    // Store mask
    _history[_index] = mask;
    _index = (_index + 1) % HISTORY_LEN;
    if (_count < HISTORY_LEN) _count++;

    // Need at least HISTORY_LEN samples
    if (_count < HISTORY_LEN) return false;

    // Count how many are all-ones (intersection pattern)
    int ones = countAllOnes();

    // Intersection if:
    // - At least 3 out of last 6 are 111 (persistence)
    // - And not all 6 are 111 (avoid false positive on a pure long intersection)
    // - And there is at least one transition (not all same) -> could be detected via pattern
    // Simpler: if ones >= 3 and ones < HISTORY_LEN (i.e., not all)
    if (ones >= 3 && ones < HISTORY_LEN) {
        return true;
    }
    return false;
}

int IntersectionDetector::countAllOnes() const {
    int cnt = 0;
    for (int i = 0; i < HISTORY_LEN; ++i) {
        if (_history[i] == 0b111) cnt++;
    }
    return cnt;
}