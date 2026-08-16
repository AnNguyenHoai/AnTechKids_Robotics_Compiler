#include "jump_if_false_instruction.h"
#include "control_instruction_common.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace control {

JumpIfFalseInstruction::JumpIfFalseInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::JUMP_IF_FALSE)) {}

ExecutionResult JumpIfFalseInstruction::execute(InstructionContext& ctx) {
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "JUMP_IF_FALSE: insufficient operands",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    RuntimeValue targetVal = ctx.context().operandStack().pop();
    RuntimeValue condVal = ctx.context().operandStack().pop();

    if (!targetVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "JUMP_IF_FALSE: target must be integer",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    if (!condVal.isBoolean()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            3,
            "JUMP_IF_FALSE: condition must be boolean",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    if (!condVal.asBoolean()) {
        uint32_t target = static_cast<uint32_t>(targetVal.asInteger());
        ctx.context().programCounter().jump(target);
    } else {
        ctx.context().programCounter().next();
    }

    return ExecutionResult(ExecutionStatus::Success);
}

bool JumpIfFalseInstruction::validate(InstructionContext& ctx) {
    return ctx.context().operandStack().size() >= 2;
}

std::string JumpIfFalseInstruction::name() const {
    return "JUMP_IF_FALSE";
}

uint32_t JumpIfFalseInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory JumpIfFalseInstruction::category() const {
    return InstructionCategory::Internal;
}

Semantic JumpIfFalseInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace control
} // namespace execution
} // namespace robot