#ifndef LIGHT_SENSOR_H
#define LIGHT_SENSOR_H

#include <Arduino.h>

class LightSensor {
public:
    LightSensor(int pin);
    void init();
    int readRaw(); // 0-4095 (ESP32 ADC)
private:
    int _pin;
};

#endif