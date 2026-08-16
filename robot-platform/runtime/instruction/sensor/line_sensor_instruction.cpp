#include "line_sensor_instruction.h"
#include "sensor_instruction_common.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace sensor {

LineSensorInstruction::LineSensorInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::ReadLine)) {}

ExecutionResult LineSensorInstruction::execute(InstructionContext& ctx) {
    if (ctx.context().operandStack().size() < 2) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "LINE_SENSOR: insufficient operands (need port and channel)",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    // Stack order: port pushed first, then channel -> top is channel
    RuntimeValue channelVal = ctx.context().operandStack().pop();
    RuntimeValue portVal = ctx.context().operandStack().pop();

    if (!portVal.isInteger() || !channelVal.isInteger()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "LINE_SENSOR: port and channel must be integers",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            m_opcode
        );
    }

    int port = portVal.asInteger();
    int channel = channelVal.asInteger();

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

    // RobotAPI::ReadLine expects only channel (port is ignored in implementation)
    RobotApiRequest request;
    request.setApiId(ApiId::READ_LINE);
    request.addParameter(RuntimeValue(channel));

    auto result = ctx.apiDispatcher().dispatch(request);

    if (result.status() != PlatformStatus::OK) {
        return result.toExecutionResult(m_opcode);
    }

    if (result.returnValue().has_value()) {
        ctx.context().operandStack().push(result.returnValue().value());
    } else {
        ctx.context().operandStack().push(RuntimeValue(0));
    }

    ctx.context().programCounter().next();
    return ExecutionResult(ExecutionStatus::Success);
}

bool LineSensorInstruction::validate(InstructionContext& ctx) {
    return ctx.context().operandStack().size() >= 2;
}

std::string LineSensorInstruction::name() const {
    return "READ_LINE";
}

uint32_t LineSensorInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory LineSensorInstruction::category() const {
    return InstructionCategory::Sensor;
}

Semantic LineSensorInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace sensor
} // namespace execution
} // namespace robot