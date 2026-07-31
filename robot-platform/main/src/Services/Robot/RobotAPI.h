/******************************************************************************
 * File        : RobotAPI.h
 *
 * Description :
 *      Robot Hardware Abstraction API.
 *
 *      Robot VM is only allowed to access robot hardware through this API.
 *
 ******************************************************************************/

#pragma once

#include <stdint.h>
#include "RobotAPI.h"
#include <Arduino.h>
#include "../../HardwareAbstraction/GPIO.h"
namespace RobotAPI
{

/******************************************************************************
 * Initialization
 ******************************************************************************/

/**
 * Initialize hardware (motor pins, PWM, etc.)
 */
void Initialize();

/******************************************************************************
 * Motion Control
 ******************************************************************************/

/**
 * Move forward.
 *
 * @param speed
 *      Motor speed (-100 to 100).
 */
void Forward(int16_t speed);

/**
 * Move backward.
 *
 * @param speed
 *      Motor speed (-100 to 100).
 */
void Backward(int16_t speed);

/**
 * Turn left.
 *
 * @param speed
 *      Motor speed (-100 to 100).
 */
void TurnLeft(int16_t speed);

/**
 * Turn right.
 *
 * @param speed
 *      Motor speed (-100 to 100).
 */
void TurnRight(int16_t speed);

/**
 * Stop robot.
 */
void Stop();

/******************************************************************************
 * Sensor
 ******************************************************************************/

/**
 * Read ultrasonic sensor.
 *
 * @return Distance (cm)
 */
int16_t ReadUltrasonic();
/**
 * Read ultrasonic sensor.
 *
 * @return distanceFront (cm)
 */
float distanceFront();
/**
 * Read ultrasonic sensor.
 *
 * @return port (bool)
 */
int16_t ReadTouch(int port);
/**
 * Read ultrasonic sensor.
 *
 * @return Distance (cm)
 */
int16_t ReadLight(int channel);
/**
 * Read ultrasonic sensor.
 *
 * @return Distance (cm)
 */
int16_t ReadColor();
/**
 * Read ultrasonic sensor.
 *
 * @return Distance (cm)
 */
int16_t ReadLine(int channel);

/******************************************************************************
 * Utility
 ******************************************************************************/

/**
 * Blocking delay.
 *
 * @param ms
 *      Delay time.
 */
void Wait(uint16_t ms);


void setMotorsDirect(int left, int right);

}