#pragma once

#include <cstdint>
#include <string>

namespace robot {
namespace execution {
namespace sensor {

// Common utilities for sensor instructions
inline bool isValidPort(int port) {
    // For now, only port 1 is valid (matching RoboSim convention)
    return port == 1;
}

inline std::string portError(int port) {
    return "Invalid sensor port: " + std::to_string(port) + " (expected 1)";
}

} // namespace sensor
} // namespace execution
} // namespace robot