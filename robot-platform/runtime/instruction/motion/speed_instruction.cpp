#include "speed_instruction.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace motion {

SpeedInstruction::SpeedInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::SET_SPEED)) {}

ExecutionResult SpeedInstruction::execute(InstructionContext& ctx) {
    // Expect operands: [left_speed, right_speed]
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "SpeedInstruction: need left and right speeds",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    RuntimeValue rightVal = ctx.context().operandStack().pop();
    RuntimeValue leftVal = ctx.context().operandStack().pop();

    if (!leftVal.isInteger() || !rightVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "SpeedInstruction: speeds must be integers",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    int left = leftVal.asInteger();
    int right = rightVal.asInteger();

    if (!isValidSpeed(left) || !isValidSpeed(right)) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            3,
            "SpeedInstruction: speed out of range [-100, 100]",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    RobotApiRequest request(ApiId::SET_SPEED, {RuntimeValue(left), RuntimeValue(right)});

    auto result = ctx.apiDispatcher().dispatch(request);

    if (result.status() == PlatformStatus::OK) {
        ctx.context().programCounter().next();
    }

    return result.toExecutionResult(m_opcode);
}

bool SpeedInstruction::validate(InstructionContext& ctx) {
    return ctx.context().operandStack().size() >= 2;
}

std::string SpeedInstruction::name() const {
    return "SET_SPEED";
}

uint32_t SpeedInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory SpeedInstruction::category() const {
    return InstructionCategory::Motion;
}

Semantic SpeedInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace motion
} // namespace execution
} // namespace robot