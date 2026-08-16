#include "load_const_handler.h"
#include "execution_types.h"
#include "runtime_value.h"

namespace robot {
namespace execution {

LoadConstHandler::LoadConstHandler() : m_opcode(static_cast<uint32_t>(Opcode::LOAD_CONST)) {}

ExecutionResult LoadConstHandler::execute(InstructionContext& ctx) {
    // Expect operand: value (integer or boolean) on stack?
    // In many VMs, LOAD_CONST pushes a constant from the instruction stream.
    // For simplicity, we will assume the constant is on the operand stack already (pushed by loader).
    // But in our framework, the instruction itself may have operands.
    // Since we don't have a bytecode representation yet, we'll simulate by reading from operand stack.
    if (ctx.context().operandStack().empty()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "LOAD_CONST: no value on operand stack",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }
    RuntimeValue val = ctx.context().operandStack().pop();
    // Push the value back? No, LOAD_CONST typically loads a constant onto stack.
    // We need to have the constant value already available. We'll simulate: the constant is the operand.
    // Better: we'll assume the loader pushed the constant onto stack before executing LOAD_CONST.
    // For now, we'll just push the same value again (simulate loading).
    ctx.context().operandStack().push(val);
    ctx.context().programCounter().next();
    return ExecutionResult(ExecutionStatus::Success);
}

bool LoadConstHandler::validate(InstructionContext& ctx) {
    return !ctx.context().operandStack().empty();
}

std::string LoadConstHandler::name() const { return "LOAD_CONST"; }
uint32_t LoadConstHandler::opcode() const { return m_opcode; }
InstructionCategory LoadConstHandler::category() const { return InstructionCategory::Internal; }
Semantic LoadConstHandler::semantic() const { return Semantic::Native; }

} // namespace execution
} // namespace robot