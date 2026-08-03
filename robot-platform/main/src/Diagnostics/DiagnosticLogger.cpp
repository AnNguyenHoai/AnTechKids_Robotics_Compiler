#include "DiagnosticLogger.h"
#include <Arduino.h>

void DiagnosticLogger::printSeparator() {
    Serial.println("==============================");
}

void DiagnosticLogger::printHeader(const char* title) {
    Serial.println(title);
}

void DiagnosticLogger::printSensor(const char* name, const SensorStatistics& stat) {
    Serial.printf("--- %s ---\n", name);
    Serial.printf("Reads          %u\n", stat.readCount);
    Serial.printf("HIGH           %u\n", stat.highCount);
    Serial.printf("LOW            %u\n", stat.lowCount);
    Serial.printf("Transitions    %u\n", stat.transitionCount);
    Serial.printf("Stability      %.1f%%\n", stat.stability);
}

void DiagnosticLogger::printRuntime(uint32_t tickCount, float freqHz,
                                    uint32_t lastUs, uint32_t minUs, uint32_t maxUs) {
    Serial.println("--- Runtime ---");
    Serial.printf("Ticks          %u\n", tickCount);
    Serial.printf("Loop freq      %.2f Hz\n", freqHz);
    Serial.printf("Last loop      %u us\n", lastUs);
    Serial.printf("Min loop       %u us\n", minUs);
    Serial.printf("Max loop       %u us\n", maxUs);
}