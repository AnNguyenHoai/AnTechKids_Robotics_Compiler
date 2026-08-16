# Relative Heading Estimator

## Overview

The HeadingEstimator computes the robot's relative heading (yaw) by integrating the calibrated gyroscope Z-axis angular velocity from the MPU6050.

## Coordinate Convention

- **Positive gyroZ**: left rotation (counter-clockwise) → heading increases.
- **Negative gyroZ**: right rotation (clockwise) → heading decreases.

This convention is consistent with the physical robot tests.

## Calibration Requirement

**Important:** Heading estimation is only enabled after the gyroscope has been successfully calibrated.

- The `HeadingEstimator` will not integrate gyro data if the IMU is not calibrated.
- Upon successful calibration, the estimator is automatically reset to 0°.
- This prevents drift due to uncalibrated bias and ensures heading starts from a known reference.

## Integration Formula
heading += gyroZ * dt

text

Where:
- `gyroZ` in degrees per second (°/s)
- `dt` in seconds

## Timestamp Handling

- Uses `IMUSample.timestamp` (milliseconds, from `millis()`).
- First sample only establishes initial timestamp; no integration.
- Subsequent samples compute `dt = currentTimestamp - previousTimestamp`.

## Protection

- If `dt <= 0`: sample ignored.
- If `dt > MAX_DT (0.1s)`: sample ignored to prevent huge jumps.
- Only valid samples (valid flag true) are processed.

## Heading Representation

- Internal heading is a floating-point value in degrees.
- No automatic normalization to 0-360 or -180-180; allows accumulation beyond 360°.

## Serial Commands

- `heading status`: displays current heading, last gyroZ, last dt, timestamp, initialization status, and IMU calibration status.

## Integration with Platform

- `HeadingEstimator` is updated in the main loop after `SensorManager.updateAll()`.
- It consumes `IMUSample` from `IMUSensor`, not performing its own I2C reads.
- Update only occurs when `IMUSensor::isCalibrated()` returns true.

## Dependencies

- `IMUSensor` (MPU6050)
- No motor, PID, or VM dependencies.

## Known Limitations

- Gyro drift: heading will drift over time due to bias/offset.
- No magnetometer or accelerometer fusion; pure gyro integration.
- Accuracy limited by gyro noise and calibration.

## Physical Test Results

(To be filled after testing)

- 30° left: +...°
- 30° right: -...°
- 90° left: +...°
- 90° right: -...°
- 180°: ±...°
- Drift test (60s stationary): ...°

## Future

M5.6.3 will implement a Heading Hold Controller using this estimator.