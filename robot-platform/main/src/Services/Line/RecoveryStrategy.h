#ifndef RECOVERY_STRATEGY_H
#define RECOVERY_STRATEGY_H

#include <stdint.h>

class RecoveryStrategy {
public:
    RecoveryStrategy();

    void update(uint8_t mask, int &left, int &right);
    void reset();

private:
    enum Phase { SEARCH_LEFT, SEARCH_RIGHT, SEARCH_SPIRAL };
    Phase _phase;
    uint32_t _phaseStart;
    int _speed;
};

#endif