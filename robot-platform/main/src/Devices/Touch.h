#ifndef TOUCH_H
#define TOUCH_H

#include <Arduino.h>

class Touch {
public:
    Touch(int pin);
    void init();
    bool read();
private:
    int _pin;
};

#endif