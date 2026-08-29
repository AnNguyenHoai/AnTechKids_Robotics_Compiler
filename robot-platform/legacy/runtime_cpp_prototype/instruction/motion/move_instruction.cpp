#include "move_instruction.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace motion {

MoveInstruction::MoveInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::FORWARD)) {
    // In a real implementation, we might have separate handlers for each direction.
    // For now, we'll use one handler and parse direction from operands.
}

ExecutionResult MoveInstruction::execute(InstructionContext& ctx) {
    // Expect operands: [direction (uint32_t), speed (int32_t), duration (uint32_t) optional]
    // For simplicity, we'll assume direction and speed are on operand stack.
    // In a real system, operands would come from instruction decoding.
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "MoveInstruction: insufficient operands (need direction and speed)",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    // Pop operands: direction is first (stack: [direction, speed] -> pop speed then direction)
    // But we'll pop direction first? Let's define order: push direction, then speed.
    // So stack top is speed, then direction.
    RuntimeValue speedVal = ctx.context().operandStack().pop();
    RuntimeValue dirVal = ctx.context().operandStack().pop();

    if (!dirVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "MoveInstruction: direction must be integer",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }
    if (!speedVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            3,
            "MoveInstruction: speed must be integer",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    int directionInt = dirVal.asInteger();
    int speed = speedVal.asInteger();

    if (!isValidSpeed(speed)) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            4,
            "MoveInstruction: speed out of range [-100, 100]",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    // Map direction integer to ApiId
    ApiId apiId;
    switch (directionInt) {
        case 0: apiId = ApiId::FORWARD; break;
        case 1: apiId = ApiId::BACKWARD; break;
        case 2: apiId = ApiId::TURN_LEFT; break;
        case 3: apiId = ApiId::TURN_RIGHT; break;
        default:
            return ExecutionResult(
                ExecutionStatus::Failure,
                5,
                "MoveInstruction: invalid direction",
                ctx.context().programCounter().current(),
                ExecutionLayer::Dispatcher,
                m_opcode
            );
    }

    // Build RobotApiRequest
    RobotApiRequest request(apiId, {RuntimeValue(speed)});

    // Dispatch via RobotApiDispatcher
    auto result = ctx.apiDispatcher().dispatch(request);

    // Advance PC if success
    if (result.status() == PlatformStatus::OK) {
        ctx.context().programCounter().next();
    }

    // Convert to ExecutionResult
    return result.toExecutionResult(m_opcode);
}

bool MoveInstruction::validate(InstructionContext& ctx) {
    // Basic validation: ensure at least 2 operands on stack
    return ctx.context().operandStack().size() >= 2;
}

std::string MoveInstruction::name() const {
    return "MOVE";
}

uint32_t MoveInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory MoveInstruction::category() const {
    return InstructionCategory::Motion;
}

Semantic MoveInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace motion
} // namespace execution
} // namespace robot