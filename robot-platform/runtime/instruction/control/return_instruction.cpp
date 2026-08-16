#include "return_instruction.h"
#include "execution_context.h"

namespace robot {
namespace execution {
namespace control {

ReturnInstruction::ReturnInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::RETURN)) {}

ExecutionResult ReturnInstruction::execute(InstructionContext& ctx) {
    if (ctx.context().callStack().empty()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "RETURN: call stack empty",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    StackFrame frame = ctx.context().callStack().popFrame();
    ctx.context().programCounter().jump(frame.returnAddress);

    // Optionally restore local variable scope etc. (not implemented yet)
    return ExecutionResult(ExecutionStatus::Success);
}

bool ReturnInstruction::validate(InstructionContext& ctx) {
    return !ctx.context().callStack().empty();
}

std::string ReturnInstruction::name() const {
    return "RETURN";
}

uint32_t ReturnInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory ReturnInstruction::category() const {
    return InstructionCategory::Internal;
}

Semantic ReturnInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace control
} // namespace execution
} // namespace robot