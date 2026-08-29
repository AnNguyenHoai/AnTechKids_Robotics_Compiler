#include "jump_instruction.h"
#include "control_instruction_common.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace control {

JumpInstruction::JumpInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::JUMP)) {}

ExecutionResult JumpInstruction::execute(InstructionContext& ctx) {
    // Expect operand: target address (uint32_t) on operand stack
    if (ctx.context().operandStack().empty()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "JUMP: no target on operand stack",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    RuntimeValue targetVal = ctx.context().operandStack().pop();
    if (!targetVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "JUMP: target must be integer",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    uint32_t target = static_cast<uint32_t>(targetVal.asInteger());

    // Validate target (program size not known here; will be validated by VM)
    // We just set PC; VM will check bounds later.
    ctx.context().programCounter().jump(target);
    return ExecutionResult(ExecutionStatus::Success);
}

bool JumpInstruction::validate(InstructionContext& ctx) {
    // Ensure at least one operand on stack
    return !ctx.context().operandStack().empty();
}

std::string JumpInstruction::name() const {
    return "JUMP";
}

uint32_t JumpInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory JumpInstruction::category() const {
    return InstructionCategory::Internal;
}

Semantic JumpInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace control
} // namespace execution
} // namespace robot