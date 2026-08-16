#include "wait_handler.h"
#include "execution_types.h"

namespace robot {
namespace execution {

WaitHandler::WaitHandler() : m_opcode(static_cast<uint32_t>(Opcode::WAIT)) {}

ExecutionResult WaitHandler::execute(InstructionContext& ctx) {
    // In future, this will set a timer and yield.
    // For now, just advance PC (no blocking).
    ctx.context().flags().setWaiting(true);
    // In real implementation, we would set a wakeup time.
    // For core instruction test, we just advance.
    ctx.context().programCounter().next();
    return ExecutionResult(ExecutionStatus::Success, 0, "WAIT executed (non-blocking)");
}

bool WaitHandler::validate(InstructionContext& ctx) {
    return true;
}

std::string WaitHandler::name() const { return "WAIT"; }
uint32_t WaitHandler::opcode() const { return m_opcode; }
InstructionCategory WaitHandler::category() const { return InstructionCategory::Internal; }
Semantic WaitHandler::semantic() const { return Semantic::Native; }

} // namespace execution
} // namespace robot