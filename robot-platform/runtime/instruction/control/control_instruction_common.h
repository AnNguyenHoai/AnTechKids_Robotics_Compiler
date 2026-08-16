#pragma once

#include <cstdint>
#include <string>

namespace robot {
namespace execution {
namespace control {

// Common validation utilities for control instructions
inline bool isValidJumpTarget(uint32_t target, size_t programSize) {
    return target < programSize;
}

// Helper to format error messages
inline std::string jumpTargetError(uint32_t target, size_t programSize) {
    return "Invalid jump target: " + std::to_string(target) +
           " (program size: " + std::to_string(programSize) + ")";
}

} // namespace control
} // namespace execution
} // namespace robot