#include "turn_instruction.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace motion {

TurnInstruction::TurnInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::TURN_LEFT)) {
    // We'll use a single handler and determine direction from operand.
}

ExecutionResult TurnInstruction::execute(InstructionContext& ctx) {
    // Expect operands: [direction (0=left, 1=right), speed, angle (optional)]
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "TurnInstruction: insufficient operands (need direction and speed)",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    RuntimeValue speedVal = ctx.context().operandStack().pop();
    RuntimeValue dirVal = ctx.context().operandStack().pop();

    if (!dirVal.isInteger() || !speedVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "TurnInstruction: operands must be integers",
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
            3,
            "TurnInstruction: speed out of range [-100, 100]",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    ApiId apiId;
    switch (directionInt) {
        case 0: apiId = ApiId::TURN_LEFT; break;
        case 1: apiId = ApiId::TURN_RIGHT; break;
        default:
            return ExecutionResult(
                ExecutionStatus::Failure,
                4,
                "TurnInstruction: invalid direction (0=left, 1=right)",
                ctx.context().programCounter().current(),
                ExecutionLayer::Dispatcher,
                m_opcode
            );
    }

    // Check optional angle operand (if present)
    std::vector<RuntimeValue> params;
    params.push_back(RuntimeValue(speed));
    if (!ctx.context().operandStack().empty()) {
        // Optional angle
        RuntimeValue angleVal = ctx.context().operandStack().pop();
        if (angleVal.isInteger()) {
            params.push_back(angleVal);
        }
    }

    RobotApiRequest request(apiId, params);

    auto result = ctx.apiDispatcher().dispatch(request);

    if (result.status() == PlatformStatus::OK) {
        ctx.context().programCounter().next();
    }

    return result.toExecutionResult(m_opcode);
}

bool TurnInstruction::validate(InstructionContext& ctx) {
    return ctx.context().operandStack().size() >= 2;
}

std::string TurnInstruction::name() const {
    return "TURN";
}

uint32_t TurnInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory TurnInstruction::category() const {
    return InstructionCategory::Motion;
}

Semantic TurnInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace motion
} // namespace execution
} // namespace robot