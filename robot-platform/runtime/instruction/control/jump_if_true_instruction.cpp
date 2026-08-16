#include "jump_if_true_instruction.h"
#include "control_instruction_common.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace control {

JumpIfTrueInstruction::JumpIfTrueInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::JUMP_IF_TRUE)) {}

ExecutionResult JumpIfTrueInstruction::execute(InstructionContext& ctx) {
    // Expect two operands: condition (bool) and target (uint32_t)
    // Stack order: condition pushed first, then target (top is target)
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "JUMP_IF_TRUE: insufficient operands",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    // Pop target first (top is target)
    RuntimeValue targetVal = ctx.context().operandStack().pop();
    // Then condition
    RuntimeValue condVal = ctx.context().operandStack().pop();

    if (!targetVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "JUMP_IF_TRUE: target must be integer",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    if (!condVal.isBoolean()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            3,
            "JUMP_IF_TRUE: condition must be boolean",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    if (condVal.asBoolean()) {
        uint32_t target = static_cast<uint32_t>(targetVal.asInteger());
        ctx.context().programCounter().jump(target);
    } else {
        ctx.context().programCounter().next();
    }

    return ExecutionResult(ExecutionStatus::Success);
}

bool JumpIfTrueInstruction::validate(InstructionContext& ctx) {
    return ctx.context().operandStack().size() >= 2;
}

std::string JumpIfTrueInstruction::name() const {
    return "JUMP_IF_TRUE";
}

uint32_t JumpIfTrueInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory JumpIfTrueInstruction::category() const {
    return InstructionCategory::Internal;
}

Semantic JumpIfTrueInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace control
} // namespace execution
} // namespace robot