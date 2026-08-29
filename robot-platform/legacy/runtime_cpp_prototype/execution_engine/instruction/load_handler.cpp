#include "load_handler.h"
#include "execution_types.h"
#include "runtime_value.h"

namespace robot {
namespace execution {

LoadHandler::LoadHandler() : m_opcode(static_cast<uint32_t>(Opcode::LOAD)) {}

ExecutionResult LoadHandler::execute(InstructionContext& ctx) {
    // Expect operand: variable id (uint32_t)
    if (ctx.context().operandStack().empty()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "LOAD: no variable id on stack",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }
    RuntimeValue idVal = ctx.context().operandStack().pop();
    if (!idVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "LOAD: variable id must be integer",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }
    VariableId id = static_cast<VariableId>(idVal.asInteger());
    if (!ctx.context().variableTable().exists(id)) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            3,
            "LOAD: variable not found",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }
    RuntimeValue val = ctx.context().variableTable().read(id);
    ctx.context().operandStack().push(val);
    ctx.context().programCounter().next();
    return ExecutionResult(ExecutionStatus::Success);
}

bool LoadHandler::validate(InstructionContext& ctx) {
    return !ctx.context().operandStack().empty();
}

std::string LoadHandler::name() const { return "LOAD"; }
uint32_t LoadHandler::opcode() const { return m_opcode; }
InstructionCategory LoadHandler::category() const { return InstructionCategory::Internal; }
Semantic LoadHandler::semantic() const { return Semantic::Native; }

} // namespace execution
} // namespace robot