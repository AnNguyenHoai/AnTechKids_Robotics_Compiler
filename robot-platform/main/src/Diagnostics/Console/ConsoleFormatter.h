#ifndef CONSOLE_FORMATTER_H
#define CONSOLE_FORMATTER_H

#include "ConsoleData.h"
#include <Arduino.h>

class ConsoleFormatter {
public:
    static String format(const ConsoleData& data);
};

#endif