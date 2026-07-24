#ifndef LINE_SENSOR_H
#define LINE_SENSOR_H

#include <Arduino.h>

class LineSensor {
public:
    LineSensor(int leftPin, int centerPin, int rightPin);
    void init();
    bool readLeft();
    bool readCenter();
    bool readRight();
private:
    int _leftPin, _centerPin, _rightPin;
};

#endif