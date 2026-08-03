#ifndef CONSOLE_OUTPUT_H
#define CONSOLE_OUTPUT_H

#include <Arduino.h>

class ConsoleOutput {
public:
    static void begin();
    static void print(const String& message);
};

#endif