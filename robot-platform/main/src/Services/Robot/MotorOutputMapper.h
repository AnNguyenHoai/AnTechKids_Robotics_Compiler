#pragma once

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

    // Pair-aware mapping for differential steering. The stronger wheel owns
    // the physical start/run-range mapping and remains >= minDrive. The weaker
    // wheel preserves the logical ratio below minDrive when needed so line
    // following retains enough yaw authority for sharp corners.
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

} // namespace RobotAPI
