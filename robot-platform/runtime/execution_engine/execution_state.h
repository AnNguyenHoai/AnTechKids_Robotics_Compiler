#pragma once

namespace robot {
namespace execution {

enum class ExecutionState {
    Created,
    Loaded,
    Initialized,
    Ready,
    Running,
    Paused,
    Waiting,
    Completed,
    Stopped,
    Error
};

} // namespace execution
} // namespace robot