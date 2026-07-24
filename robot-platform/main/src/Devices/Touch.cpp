#include "Touch.h"

Touch::Touch(int pin) : _pin(pin) {}

void Touch::init() { pinMode(_pin, INPUT); }

bool Touch::read() { return digitalRead(_pin) == HIGH; }