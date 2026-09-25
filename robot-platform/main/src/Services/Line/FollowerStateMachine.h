#ifndef FOLLOWER_STATE_MACHINE_H
#define FOLLOWER_STATE_MACHINE_H

#include <stdint.h>
#include "LineTypes.h"

enum class FollowerState : uint8_t {
    FOLLOWING,
    LOST,
    SEARCHING,
    INTERSECTION,
    TURNING
};

class FollowerStateMachine {
public:
    FollowerStateMachine();

    // State and intent
    FollowerState getState() const { return _state; }
    MotionIntent getMotionIntent() const;

    // Update with new sensor mask and events
    void update(uint8_t mask, bool intersectionDetected, bool turnRequested, bool stopRequested);

    // External commands
    void requestTurn(int direction); // 1 = left, 2 = right
    void requestStopAtIntersection();
    void reset();

private:
    FollowerState _state;
    bool _turnRequested;
    int _turnDirection;      // 1 left, 2 right
    bool _stopRequested;
    uint32_t _lostTimer;
    bool _searchingDirection; // 0 left first, 1 right first
    uint8_t _lostCandidateSamples;

    void transitionTo(FollowerState newState);
};

#endif
