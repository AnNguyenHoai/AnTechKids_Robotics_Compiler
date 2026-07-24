#ifndef ULTRASONIC_H
#define ULTRASONIC_H

#include <Arduino.h>

class Ultrasonic {
public:
    Ultrasonic(int trigPin, int echoPin);
    void init();
    int readDistance(); // cm
private:
    int _trigPin, _echoPin;
};

#endif