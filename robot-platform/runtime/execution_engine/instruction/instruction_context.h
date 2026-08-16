#pragma once

#include "execution_context.h"
#include "runtime_services.h"
#include "../robot_dispatcher/robot_api_dispatcher.h"
#include <memory>

namespace robot {
namespace execution {

class InstructionContext {
public:
    InstructionContext(ExecutionContext& context,
                       RuntimeServices& services,
                       RobotApiDispatcher& apiDispatcher);

    ExecutionContext& context() const;
    RuntimeServices& services() const;
    RobotApiDispatcher& apiDispatcher() const;

private:
    ExecutionContext& m_context;
    RuntimeServices& m_services;
    RobotApiDispatcher& m_apiDispatcher;
};

} // namespace execution
} // namespace robot