#pragma once
#include <Arduino.h>

class Diagnostic {
public:
    static void runAll();
    static void checkBattery();
    static void checkMotor();
    static void checkFlash();
    static void checkMemory();
    static void checkClock();
};