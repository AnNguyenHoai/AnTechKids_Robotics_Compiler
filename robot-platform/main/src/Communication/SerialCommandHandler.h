#ifndef SERIAL_COMMAND_HANDLER_H
#define SERIAL_COMMAND_HANDLER_H

#include <Arduino.h>

class SerialCommandHandler {
public:
    static void setup();
    static void handle();  // call in loop
};

#endif