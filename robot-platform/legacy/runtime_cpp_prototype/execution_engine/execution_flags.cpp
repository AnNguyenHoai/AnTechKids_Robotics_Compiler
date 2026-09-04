#include "execution_flags.h"

namespace robot {
namespace execution {

ExecutionFlags::ExecutionFlags()
    : m_running(false), m_paused(false), m_waiting(false),
      m_completed(false), m_error(false), m_interrupted(false),
      m_breakpoint(false), m_suspended(false) {}

void ExecutionFlags::setRunning(bool running) { m_running = running; }
void ExecutionFlags::setPaused(bool paused) { m_paused = paused; }
void ExecutionFlags::setWaiting(bool waiting) { m_waiting = waiting; }
void ExecutionFlags::setCompleted(bool completed) { m_completed = completed; }
void ExecutionFlags::setError(bool error) { m_error = error; }
void ExecutionFlags::setInterrupted(bool interrupted) { m_interrupted = interrupted; }
void ExecutionFlags::setBreakpoint(bool breakpoint) { m_breakpoint = breakpoint; }
void ExecutionFlags::setSuspended(bool suspended) { m_suspended = suspended; }

bool ExecutionFlags::isRunning() const { return m_running; }
bool ExecutionFlags::isPaused() const { return m_paused; }
bool ExecutionFlags::isWaiting() const { return m_waiting; }
bool ExecutionFlags::isCompleted() const { return m_completed; }
bool ExecutionFlags::isError() const { return m_error; }
bool ExecutionFlags::isInterrupted() const { return m_interrupted; }
bool ExecutionFlags::isBreakpoint() const { return m_breakpoint; }
bool ExecutionFlags::isSuspended() const { return m_suspended; }

void ExecutionFlags::reset() {
    m_running = false;
    m_paused = false;
    m_waiting = false;
    m_completed = false;
    m_error = false;
    m_interrupted = false;
    m_breakpoint = false;
    m_suspended = false;
}

void ExecutionFlags::clearAll() {
    reset();
}

} // namespace execution
} // namespace robot