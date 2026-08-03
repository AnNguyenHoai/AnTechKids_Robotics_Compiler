#ifndef CONSOLE_DATA_H
#define CONSOLE_DATA_H

#include "../SensorStatistics.h"
#include <stdint.h>

struct ConsoleData {
    // Sensor states (0/1)
    uint8_t leftState;
    uint8_t centerState;
    uint8_t rightState;
    uint8_t mask; // 3-bit: bit2=left, bit1=center, bit0=right

    // Statistics
    SensorStatistics leftStat;
    SensorStatistics centerStat;
    SensorStatistics rightStat;

    // Runtime
    uint32_t tickCount;
    float loopFreq;
    uint32_t lastLoopUs;
    uint32_t minLoopUs;
    uint32_t maxLoopUs;
};

#endif