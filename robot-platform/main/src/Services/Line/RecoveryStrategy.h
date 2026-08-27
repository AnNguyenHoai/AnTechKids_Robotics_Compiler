#ifndef RECOVERY_STRATEGY_H
#define RECOVERY_STRATEGY_H

#include <stdint.h>

class RecoveryStrategy {
public:
    enum Direction { DIR_UNKNOWN = 0, DIR_LEFT = -1, DIR_RIGHT = 1 };

    RecoveryStrategy();
    void update(uint8_t mask, int &left, int &right);
    void reset();
    void setLastDirection(Direction direction);

private:
    enum Phase { SOFT_SEARCH, DEEP_SEARCH, SWEEP };
    Phase _phase;
    uint32_t _phaseStart;
    Direction _lastDirection;
};

#endif
