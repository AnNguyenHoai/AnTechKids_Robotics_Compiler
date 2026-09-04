#include "nop_handler.h"
#include "execution_types.h"

namespace robot {
namespace execution {

NopHandler::NopHandler() : m_opcode(static_cast<uint32_t>(Opcode::NOP)) {}

ExecutionResult NopHandler::execute(InstructionContext& ctx) {
    // Advance PC
    ctx.context().programCounter().next();
    return ExecutionResult(ExecutionStatus::Success, 0, "NOP executed");
}

bool NopHandler::validate(InstructionContext& ctx) {
    return true;
}

std::string NopHandler::name() const { return "NOP"; }
uint32_t NopHandler::opcode() const { return m_opcode; }
InstructionCategory NopHandler::category() const { return InstructionCategory::Internal; }
Semantic NopHandler::semantic() const { return Semantic::Native; }

} // namespace execution
} // namespace robot