#pragma once

#include "execution_state.h"

namespace robot {
namespace execution {

class Scheduler {
public:
    Scheduler();

    void start();
    void pause();
    void resume();
    void stop();

    ExecutionState getState() const;
    void reset();

private:
    ExecutionState m_state;
};

} // namespace execution
} // namespace robot