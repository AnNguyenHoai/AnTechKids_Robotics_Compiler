#ifndef COLOR_SENSOR_H
#define COLOR_SENSOR_H

#include <Arduino.h>

class ColorSensor {
public:
    void init();
    int readColor(); // dummy
};

#endif