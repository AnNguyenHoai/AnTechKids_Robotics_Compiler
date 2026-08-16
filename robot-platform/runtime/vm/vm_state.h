#pragma once

#include <cstdint>

namespace robot {
namespace execution {

enum class VMState : uint8_t {
    Created,
    Loaded,
    Ready,
    Running,
    Paused,
    Completed,
    Stopped,
    Error
};

} // namespace execution
} // namespace robot