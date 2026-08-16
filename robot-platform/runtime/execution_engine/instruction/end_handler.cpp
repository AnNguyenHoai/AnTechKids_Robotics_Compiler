#include "end_handler.h"
#include "execution_types.h"

namespace robot {
namespace execution {

EndHandler::EndHandler() : m_opcode(static_cast<uint32_t>(Opcode::END)) {}

ExecutionResult EndHandler::execute(InstructionContext& ctx) {
    ctx.context().flags().setCompleted(true);
    ctx.context().setState(ExecutionState::Completed);
    // Do not advance PC; execution engine will stop.
    return ExecutionResult(ExecutionStatus::Success, 0, "END executed");
}

bool EndHandler::validate(InstructionContext& ctx) {
    return true;
}

std::string EndHandler::name() const { return "END"; }
uint32_t EndHandler::opcode() const { return m_opcode; }
InstructionCategory EndHandler::category() const { return InstructionCategory::Internal; }
Semantic EndHandler::semantic() const { return Semantic::Native; }

} // namespace execution
} // namespace robot