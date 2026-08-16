#include "instruction_context.h"

namespace robot {
namespace execution {

InstructionContext::InstructionContext(ExecutionContext& context,
                                       RuntimeServices& services,
                                       RobotApiDispatcher& apiDispatcher)
    : m_context(context), m_services(services), m_apiDispatcher(apiDispatcher) {}

ExecutionContext& InstructionContext::context() const {
    return m_context;
}

RuntimeServices& InstructionContext::services() const {
    return m_services;
}

RobotApiDispatcher& InstructionContext::apiDispatcher() const {
    return m_apiDispatcher;
}

} // namespace execution
} // namespace robot