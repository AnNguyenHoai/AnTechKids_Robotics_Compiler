#pragma once

#include <cstdint>
#include <string>

namespace robot {
namespace execution {
namespace motion {

// Direction constants
enum class Direction : uint8_t {
    Forward,
    Backward,
    Left,
    Right
};

// Helper to convert Direction to string (for diagnostics)
inline std::string directionToString(Direction dir) {
    switch (dir) {
        case Direction::Forward: return "Forward";
        case Direction::Backward: return "Backward";
        case Direction::Left: return "Left";
        case Direction::Right: return "Right";
        default: return "Unknown";
    }
}

// Speed range validation
inline bool isValidSpeed(int speed) {
    return speed >= -100 && speed <= 100;
}

// Duration range validation (milliseconds)
inline bool isValidDuration(uint32_t duration) {
    // Accept any non-zero duration; 0 is allowed as "indefinite"
    return true;
}

} // namespace motion
} // namespace execution
} // namespace robot