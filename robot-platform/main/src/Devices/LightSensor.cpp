#include "LightSensor.h"

LightSensor::LightSensor(int pin) : _pin(pin) {}

void LightSensor::init() { pinMode(_pin, INPUT); }

int LightSensor::readRaw() { return analogRead(_pin); }