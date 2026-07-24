#ifndef BEHAVIOR_CONTEXT_H
#define BEHAVIOR_CONTEXT_H

#include <stdint.h>
#include "../Services/Robot/RobotAPI.h"

class BehaviorContext {
public:
    BehaviorContext() : timestamp(0) {}

    uint32_t getTimestamp() const { return timestamp; }
    void updateTimestamp() { timestamp = millis(); }

    // Motion APIs
    void forward(int speed) { RobotAPI::Forward(speed); }
    void backward(int speed) { RobotAPI::Backward(speed); }
    void turnLeft(int speed) { RobotAPI::TurnLeft(speed); }
    void turnRight(int speed) { RobotAPI::TurnRight(speed); }
    void stop() { RobotAPI::Stop(); }
    void wait(uint16_t ms) { RobotAPI::Wait(ms); }

    // Sensor APIs
    int16_t readUltrasonic() { return RobotAPI::ReadUltrasonic(); }
    int16_t readTouch(int port) { return RobotAPI::ReadTouch(port); }
    int16_t readLight(int channel) { return RobotAPI::ReadLight(channel); }
    int16_t readColor() { return RobotAPI::ReadColor(); }
    int16_t readLine(int channel) { return RobotAPI::ReadLine(channel); }

private:
    uint32_t timestamp;
};

#endif