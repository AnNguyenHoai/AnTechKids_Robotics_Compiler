#include "compare_instruction.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace control {

CompareInstruction::CompareInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::COMPARE_EQ)) {
    // We'll use one handler for all compare opcodes; the specific opcode
    // is determined by the instruction's opcode.
}

ExecutionResult CompareInstruction::execute(InstructionContext& ctx) {
    // Expect three operands: left, right, result index (or three values on stack)
    // For simplicity, we assume operands are on operand stack:
    // push left, push right, then execute compare -> pop both, compute, push result
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "COMPARE: insufficient operands",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    // Pop right then left (stack order: left then right -> top is right)
    RuntimeValue rightVal = ctx.context().operandStack().pop();
    RuntimeValue leftVal = ctx.context().operandStack().pop();

    // Determine comparison operator from opcode
    uint32_t op = m_opcode;
    bool result = false;

    // Compare based on types
    if (leftVal.isInteger() && rightVal.isInteger()) {
        int64_t l = leftVal.asInteger();
        int64_t r = rightVal.asInteger();
        switch (op) {
            case static_cast<uint32_t>(Opcode::COMPARE_EQ): result = (l == r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_NE): result = (l != r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_LT): result = (l < r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_LE): result = (l <= r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_GT): result = (l > r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_GE): result = (l >= r); break;
            default:
                return ExecutionResult(
                    ExecutionStatus::Failure,
                    2,
                    "COMPARE: unsupported opcode",
                    ctx.context().programCounter().current(),
                    ExecutionLayer::Dispatcher,
                    m_opcode
                );
        }
    } else if (leftVal.isFloat() && rightVal.isFloat()) {
        float l = leftVal.asFloat();
        float r = rightVal.asFloat();
        switch (op) {
            case static_cast<uint32_t>(Opcode::COMPARE_EQ): result = (l == r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_NE): result = (l != r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_LT): result = (l < r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_LE): result = (l <= r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_GT): result = (l > r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_GE): result = (l >= r); break;
            default:
                return ExecutionResult(
                    ExecutionStatus::Failure,
                    3,
                    "COMPARE: unsupported opcode",
                    ctx.context().programCounter().current(),
                    ExecutionLayer::Dispatcher,
                    m_opcode
                );
        }
    } else if (leftVal.isBoolean() && rightVal.isBoolean()) {
        bool l = leftVal.asBoolean();
        bool r = rightVal.asBoolean();
        switch (op) {
            case static_cast<uint32_t>(Opcode::COMPARE_EQ): result = (l == r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_NE): result = (l != r); break;
            default:
                return ExecutionResult(
                    ExecutionStatus::Failure,
                    4,
                    "COMPARE: boolean only supports == and !=",
                    ctx.context().programCounter().current(),
                    ExecutionLayer::Dispatcher,
                    m_opcode
                );
        }
    } else if (leftVal.isString() && rightVal.isString()) {
        std::string l = leftVal.asString();
        std::string r = rightVal.asString();
        switch (op) {
            case static_cast<uint32_t>(Opcode::COMPARE_EQ): result = (l == r); break;
            case static_cast<uint32_t>(Opcode::COMPARE_NE): result = (l != r); break;
            default:
                return ExecutionResult(
                    ExecutionStatus::Failure,
                    5,
                    "COMPARE: string only supports == and !=",
                    ctx.context().programCounter().current(),
                    ExecutionLayer::Dispatcher,
                    m_opcode
                );
        }
    } else {
        return ExecutionResult(
            ExecutionStatus::Failure,
            6,
            "COMPARE: incompatible types",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    // Push result (boolean) back onto stack
    ctx.context().operandStack().push(RuntimeValue(result));

    // Advance PC
    ctx.context().programCounter().next();

    return ExecutionResult(ExecutionStatus::Success);
}

bool CompareInstruction::validate(InstructionContext& ctx) {
    return ctx.context().operandStack().size() >= 2;
}

std::string CompareInstruction::name() const {
    return "COMPARE";
}

uint32_t CompareInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory CompareInstruction::category() const {
    return InstructionCategory::Internal;
}

Semantic CompareInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace control
} // namespace execution
} // namespace robot