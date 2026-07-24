#pragma once
#include <Arduino.h>

class BootLogger {
public:
    static void log(const char* level, const char* message) {
        Serial.print("[");
        Serial.print(millis());
        Serial.print("] ");
        Serial.print(level);
        Serial.print(": ");
        Serial.println(message);
    }

    static void logFormat(const char* level, const char* format, ...) {
        char buffer[128];
        va_list args;
        va_start(args, format);
        vsnprintf(buffer, sizeof(buffer), format, args);
        va_end(args);
        log(level, buffer);
    }
};