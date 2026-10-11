#pragma once
#include <stdint.h>

namespace RobotAPI {

/**
 * H23-B: Maps logical motor commands to the raw motor speed domain.
 *
 * Input domain:  [-100, 100]
 * Output domain: [-100, 100]
 *
 * Zero is always a true stop. Any non-zero logical command is first
 * calibrated, then lifted into [minDrive, 100]. This prevents calibration
 * from dropping a commanded motor back into the measured stall region.
 */
class MotorOutputMapper {
public:
    static int map(int logicalSpeed, float speedScale, float motorScale, int minDrive);
    static int mapMagnitude(int logicalMagnitude, float scale, int minDrive);

    // Line5 steering mapping. Unlike general motion, this preserves the
    // logical 0..100 speed domain directly (plus per-motor calibration) and
    // does not lift non-zero commands into [minDrive,100]. Startup torque is
    // supplied by a short RobotAPI line-mode boost instead.
    static void mapSteeringPair(
        int logicalLeft,
        int logicalRight,
        float speedScale,
        float leftMotorScale,
        float rightMotorScale,
        int minDrive,
        int& mappedLeft,
        int& mappedRight);
};

// Stateful, Line5-only actuator policy. Do not use for generic motion.
// A wheel that must rotate stays above its measured sustainable range;
// a deliberately slowed inner wheel may instead be stopped entirely.
class LineMotorOperatingPolicy {
public:
    void reset();
    void apply(int requestedLeft, int requestedRight, uint32_t nowMs,
               int& outputLeft, int& outputRight);
private:
    struct Wheel {
        bool running = false;
        uint32_t restartAtMs = 0;
    };
    Wheel _left;
    Wheel _right;
};

} // namespace RobotAPI
