#include "IntersectionDetector.h"
#include "LineSensorLayout.h"

IntersectionDetector::IntersectionDetector() : _index(0), _count(0) {
    reset();
}

void IntersectionDetector::reset() {
    for (int i = 0; i < HISTORY_LEN; ++i) _history[i] = 0;
    _index = 0;
    _count = 0;
}

bool IntersectionDetector::update(uint8_t mask) {
    _history[_index] = LineSensorLayout::sanitizeMask(mask);
    _index = (_index + 1) % HISTORY_LEN;
    if (_count < HISTORY_LEN) _count++;

    if (_count < HISTORY_LEN) return false;

    const int candidates = countCandidates();

    // Preserve the existing temporal-persistence policy while replacing the
    // old exact 0b111 test with a five-channel candidate (>= 4 active eyes).
    // Hardware validation may tune this threshold/history in a follow-up.
    return candidates >= 3 && candidates < HISTORY_LEN;
}

int IntersectionDetector::countCandidates() const {
    int count = 0;
    for (int i = 0; i < HISTORY_LEN; ++i) {
        if (LineSensorLayout::isIntersectionCandidate(_history[i])) count++;
    }
    return count;
}