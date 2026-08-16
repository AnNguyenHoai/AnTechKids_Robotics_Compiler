#include "scheduler.h"

namespace robot {
namespace execution {

Scheduler::Scheduler() : m_state(ExecutionState::Created) {}

void Scheduler::start() {
    m_state = ExecutionState::Running;
}

void Scheduler::pause() {
    if (m_state == ExecutionState::Running) {
        m_state = ExecutionState::Paused;
    }
}

void Scheduler::resume() {
    if (m_state == ExecutionState::Paused) {
        m_state = ExecutionState::Running;
    }
}

void Scheduler::stop() {
    m_state = ExecutionState::Stopped;
}

ExecutionState Scheduler::getState() const {
    return m_state;
}

void Scheduler::reset() {
    m_state = ExecutionState::Created;
}

} // namespace execution
} // namespace robot