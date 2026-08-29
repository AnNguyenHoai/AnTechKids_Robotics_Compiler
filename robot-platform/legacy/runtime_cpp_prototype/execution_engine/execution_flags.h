#pragma once

#include <cstdint>

namespace robot {
namespace execution {

class ExecutionFlags {
public:
    ExecutionFlags();

    void setRunning(bool running);
    void setPaused(bool paused);
    void setWaiting(bool waiting);
    void setCompleted(bool completed);
    void setError(bool error);
    void setInterrupted(bool interrupted);
    void setBreakpoint(bool breakpoint);
    void setSuspended(bool suspended);

    bool isRunning() const;
    bool isPaused() const;
    bool isWaiting() const;
    bool isCompleted() const;
    bool isError() const;
    bool isInterrupted() const;
    bool isBreakpoint() const;
    bool isSuspended() const;

    void reset();
    void clearAll();

private:
    bool m_running;
    bool m_paused;
    bool m_waiting;
    bool m_completed;
    bool m_error;
    bool m_interrupted;
    bool m_breakpoint;
    bool m_suspended;
};

} // namespace execution
} // namespace robot