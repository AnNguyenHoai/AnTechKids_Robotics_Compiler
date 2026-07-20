/******************************************************************************
 * File        : RobotAPI.cpp
 *
 * Description :
 *      Robot Hardware Abstraction API Implementation.
 *
 ******************************************************************************/

#include "RobotAPI.h"

#include <Arduino.h>

namespace RobotAPI
{

/******************************************************************************
 * Motion Control
 ******************************************************************************/

void Forward(int16_t speed)
{
    Serial.print("[RobotAPI] Forward : ");
    Serial.println(speed);

    /*
     * TODO (Commit002)
     *
     * MotorDevice::Forward(speed);
     */
}

void Backward(int16_t speed)
{
    Serial.print("[RobotAPI] Backward : ");
    Serial.println(speed);
}

void TurnLeft(int16_t speed)
{
    Serial.print("[RobotAPI] TurnLeft : ");
    Serial.println(speed);
}

void TurnRight(int16_t speed)
{
    Serial.print("[RobotAPI] TurnRight : ");
    Serial.println(speed);
}

void Stop()
{
    Serial.println("[RobotAPI] Stop");
}

/******************************************************************************
 * Sensor
 ******************************************************************************/

int16_t ReadUltrasonic()
{
    Serial.println("[RobotAPI] Read Ultrasonic");

    /*
     * Prototype
     *
     * Always return 50 cm.
     */

    return 50;
}

/******************************************************************************
 * Utility
 ******************************************************************************/

void Wait(uint16_t ms)
{
    Serial.print("[RobotAPI] Wait : ");
    Serial.print(ms);
    Serial.println(" ms");

    delay(ms);
}

}