#include "stop_instruction.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"

namespace robot {
namespace execution {
namespace motion {

StopInstruction::StopInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::STOP)) {}

ExecutionResult StopInstruction::execute(InstructionContext& ctx) {
    // No operands needed
    RobotApiRequest request(ApiId::STOP, {});

    auto result = ctx.apiDispatcher().dispatch(request);

    if (result.status() == PlatformStatus::OK) {
        ctx.context().programCounter().next();
    }

    return result.toExecutionResult(m_opcode);
}

bool StopInstruction::validate(InstructionContext& ctx) {
    // Always valid
    return true;
}

std::string StopInstruction::name() const {
    return "STOP";
}

uint32_t StopInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory StopInstruction::category() const {
    return InstructionCategory::Motion;
}

Semantic StopInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace motion
} // namespace execution
} // namespace robot