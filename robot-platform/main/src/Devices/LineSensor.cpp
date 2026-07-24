#include "LineSensor.h"

LineSensor::LineSensor(int l, int c, int r) : _leftPin(l), _centerPin(c), _rightPin(r) {}

void LineSensor::init() {
    pinMode(_leftPin, INPUT);
    pinMode(_centerPin, INPUT);
    pinMode(_rightPin, INPUT);
}

bool LineSensor::readLeft() { return digitalRead(_leftPin) == HIGH; }
bool LineSensor::readCenter() { return digitalRead(_centerPin) == HIGH; }
bool LineSensor::readRight() { return digitalRead(_rightPin) == HIGH; }