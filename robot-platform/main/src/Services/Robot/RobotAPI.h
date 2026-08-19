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
// ---- Motion Output Diagnostic (DEBUG-H2-001) ----
void setMotionOutputDiagnosticEnabled(bool enabled);
bool isMotionOutputDiagnosticEnabled();
// ---- Motor PWM Diagnostic (DEBUG-H4-001) ----
void setMotorPwmDiagnosticEnabled(bool enabled);
bool isMotorPwmDiagnosticEnabled();
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
 * SetMotorSpeed.
 *
 * @param speed
 *      Motor speed (-100 to 100).
 */
void SetMotorSpeed(int left, int right);

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
void Wait(uint32_t ms);

void setMotorsDirect(int left, int right);
void SetServo(int port, int angle);
void Set3CLed(int port, int state);
void SetLightSensorLed(int port, int state);
void SetMotorStraightAngle(int leftPort, int rightPort, int speed, int angle);
void LineIntersectionStop(int speed, int type);
void SetMp3Play(int index);

int16_t GetTraceValue(int port, int channel);
bool GetTraceState(int port, int channel);
int16_t GetTraceRaw(int port);

void LineBasis(int speed);
void LineFollow(int speed);
void LineStop();
void LineTurnEncounterLine(int speed, int angle, int direction);
void LineForBmp(int speed, int degree);

// --- Heading Hold Controller ---

/**
 * Update motion with heading hold (call in main loop).
 */
void updateMotion();

/**
 * Check if heading hold is active.
 */
bool isHeadingHoldActive();

/**
 * Check if heading hold is enabled.
 */
bool isHeadingHoldEnabled();

/**
 * Enable/disable heading hold.
 */
void setHeadingHoldEnabled(bool enabled);

/**
 * Set PID gains for heading hold.
 */
void setHeadingHoldGains(float kp, float ki, float kd, float maxCorrection);

/**
 * Reset HeadingController (for calibration lifecycle).
 */
void resetHeadingController();

/**
 * Get heading control status (for diagnostics).
 */
float getHeadingTarget();
float getHeadingError();
float getHeadingCorrection();
float getHeadingKp();
float getHeadingKi();
float getHeadingKd();
float getHeadingMaxCorrection();

/**
 * Get effective motor speeds (for diagnostics).
 */
int getEffectiveLeft();
int getEffectiveRight();
int getCurrentBaseSpeed();
int getCurrentDirection();

/**
 * Get robot ready state.
 */
bool isRobotReady();

// ================================================================
// ULTRASONIC DIAGNOSTIC GETTERS
// ================================================================
/**
 * Get total number of ultrasonic read attempts.
 */
uint32_t getUltraReadCount();

/**
 * Get number of failed ultrasonic reads (timeouts).
 */
uint32_t getUltraFailCount();
// In RobotAPI.h:
void setHeadingDiagnosticEnabled(bool enabled);
bool isHeadingDiagnosticEnabled();
// ---- Heading Startup Diagnostic (DEBUG-H1-001) ----
void setHeadingStartupDiagnosticEnabled(bool enabled);
bool isHeadingStartupDiagnosticEnabled();
} // namespace RobotAPI