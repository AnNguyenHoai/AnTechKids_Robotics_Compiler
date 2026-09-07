# H24-R Recovery Merge

Base: Robotics_Stable_NoEncoder

Merged feature-only from current:
- Devices/Encoder.h/.cpp
- Sensor/QuadratureDecoder.h
- Encoder GPIO definitions
- Encoder instances and APIs in RobotAPI
- Encoder initialization
- Encoder serial bring-up commands

Intentionally retained stable versions of RobotAPI motor pipeline, MotionConfig, LineFollower path, VM and other core files.
