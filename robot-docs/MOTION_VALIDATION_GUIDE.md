# Motion Validation Guide

## Overview
This guide describes how to validate robot motion using the golden programs and validation scripts.

## Prerequisites
- ESP32 robot with motors and encoders (if available)
- USB cable
- PlatformIO or Arduino IDE
- Python 3 with pyserial installed

## Running Validation
1. Navigate to `robot-platform/validation/`.
2. Run `python motion_validation.py`.
   - This compiles each golden program, uploads to robot, reads serial log, and produces `motion_report.json`.
3. Check the report for duration of each movement.

## Interpreting Results
- For basic moves (forward/backward), duration should match the specified seconds within ±10% tolerance.
- For turns, duration may vary due to motor differences; use calibration parameters.

## Calibration
Use Serial commands to adjust `speedScale`, `leftMotorScale`, `rightMotorScale`, `turnCompensation`, and `pwmPerSpeed`.
Example:
config set speedScale 1.05
config set turnCompensation 0.9

text

## Golden Programs
All golden programs are in `robot-platform/golden/`. They should be used as regression tests for any firmware changes.