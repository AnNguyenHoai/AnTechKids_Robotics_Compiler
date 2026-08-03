#ifndef DIAGNOSTIC_LOGGER_H
#define DIAGNOSTIC_LOGGER_H

#include "SensorStatistics.h"
#include <stdint.h>

class DiagnosticLogger {
public:
    static void printSeparator();
    static void printHeader(const char* title);
    static void printSensor(const char* name, const SensorStatistics& stat);
    static void printRuntime(uint32_t tickCount, float freqHz,
                             uint32_t lastUs, uint32_t minUs, uint32_t maxUs);
};

#endif