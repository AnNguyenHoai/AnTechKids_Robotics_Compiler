#include "Ultrasonic.h"

Ultrasonic::Ultrasonic(int trigPin, int echoPin) : _trigPin(trigPin), _echoPin(echoPin) {}

void Ultrasonic::init() {
    pinMode(_trigPin, OUTPUT);
    pinMode(_echoPin, INPUT);
}

int Ultrasonic::readDistance() {
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);
    long duration = pulseIn(_echoPin, HIGH, 30000); // timeout 30ms
    if (duration == 0) return 999; // out of range
    int distance = duration * 0.034 / 2;
    return distance;
}