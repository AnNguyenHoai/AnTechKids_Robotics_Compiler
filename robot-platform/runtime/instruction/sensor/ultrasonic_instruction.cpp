#include "ultrasonic_instruction.h"
#include "sensor_instruction_common.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace sensor {

UltrasonicInstruction::UltrasonicInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::ReadUltrasonic)) {}

ExecutionResult UltrasonicInstruction::execute(InstructionContext& ctx) {
    if (ctx.context().operandStack().empty()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "ULTRASONIC: no port on operand stack",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    RuntimeValue portVal = ctx.context().operandStack().pop();
    if (!portVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "ULTRASONIC: port must be integer",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    int port = portVal.asInteger();
    if (!isValidPort(port)) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            3,
            portError(port),
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    RobotApiRequest request;
    request.setApiId(ApiId::READ_ULTRASONIC);
    request.addParameter(RuntimeValue(port));

    auto result = ctx.apiDispatcher().dispatch(request);

    if (result.status() != PlatformStatus::OK) {
        return result.toExecutionResult(m_opcode);
    }

    // Push return value if available, otherwise 0
    if (result.returnValue().has_value()) {
        ctx.context().operandStack().push(result.returnValue().value());
    } else {
        ctx.context().operandStack().push(RuntimeValue(0));
    }

    ctx.context().programCounter().next();
    return ExecutionResult(ExecutionStatus::Success);
}

bool UltrasonicInstruction::validate(InstructionContext& ctx) {
    return !ctx.context().operandStack().empty();
}

std::string UltrasonicInstruction::name() const {
    return "READ_ULTRASONIC";
}

uint32_t UltrasonicInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory UltrasonicInstruction::category() const {
    return InstructionCategory::Sensor;
}

Semantic UltrasonicInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace sensor
} // namespace execution
} // namespace robot