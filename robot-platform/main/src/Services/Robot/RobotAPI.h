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

namespace RobotAPI
{

/******************************************************************************
 * Motion Control
 ******************************************************************************/

/**
 * Move forward.
 *
 * @param speed
 *      Motor speed.
 */
void Forward(int16_t speed);

/**
 * Move backward.
 *
 * @param speed
 *      Motor speed.
 */
void Backward(int16_t speed);

/**
 * Turn left.
 *
 * @param speed
 *      Motor speed.
 */
void TurnLeft(int16_t speed);

/**
 * Turn right.
 *
 * @param speed
 *      Motor speed.
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

}