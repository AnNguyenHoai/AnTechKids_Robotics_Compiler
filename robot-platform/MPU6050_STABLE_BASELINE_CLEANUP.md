# H24-H3 — MPU6050 Stable Baseline Cleanup

## Goal
Preserve the verified MPU6050/heading behavior while removing merge-era diagnostic gates from the production path and reducing IMU read latency.

## Changes

### 1. Removed production runtime gates
Removed global flags that could disable the IMU, I2C, accel, gyro, or temperature path at runtime. A diagnostic command can no longer silently make normal IMU sampling invalid.

### 2. One coherent burst read per update
Added `MPU6050::readSample()` reading registers `0x3B..0x48` in one 14-byte I2C transaction. `IMUSensor::update()` now performs one transaction and publishes one coherent timestamped sample containing accel, temperature and gyro.

### 3. Serial `imu read`
The command now uses `IMUSensor::readSample()` instead of three independent reads.

### 4. Timing diagnostics retained
`imu timing` now reports burst sample transaction timing. Diagnostics observe timing but no longer gate production sensor operation.

### 5. Startup policy intentionally preserved
Automatic gyro calibration and the existing `g_robotReady` safety policy were not changed in this task. This avoids changing verified robot startup behavior while cleaning the MPU6050 data path.

## Validation
- No remaining references to removed `g_imu*` diagnostic gate globals in production firmware.
- Runtime update path uses `MPU6050::readSample()`.
- Heading pipeline remains `SensorManager -> IMUSensor -> latest IMUSample -> HeadingEstimator`.
