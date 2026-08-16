#include "store_handler.h"
#include "execution_types.h"
#include "runtime_value.h"

namespace robot {
namespace execution {

StoreHandler::StoreHandler() : m_opcode(static_cast<uint32_t>(Opcode::STORE)) {}

ExecutionResult StoreHandler::execute(InstructionContext& ctx) {
    // Expect two operands: variable id (uint32_t) and value (RuntimeValue)
    // We'll pop value then id (order: id pushed first? We'll define: value on top, then id below)
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "STORE: insufficient operands",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }
    // Pop id first (since stack: [..., id, value] -> pop value then id? Actually LIFO: top is value, then id below)
    RuntimeValue idVal = ctx.context().operandStack().pop();
    RuntimeValue val = ctx.context().operandStack().pop();
    if (!idVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "STORE: variable id must be integer",
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
            "STORE: variable not declared",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }
    ctx.context().variableTable().write(id, val);
    ctx.context().programCounter().next();
    return ExecutionResult(ExecutionStatus::Success);
}

bool StoreHandler::validate(InstructionContext& ctx) {
    return ctx.context().operandStack().size() >= 2;
}

std::string StoreHandler::name() const { return "STORE"; }
uint32_t StoreHandler::opcode() const { return m_opcode; }
InstructionCategory StoreHandler::category() const { return InstructionCategory::Internal; }
Semantic StoreHandler::semantic() const { return Semantic::Native; }

} // namespace execution
} // namespace robot