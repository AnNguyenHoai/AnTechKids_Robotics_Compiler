#include "touch_sensor_instruction.h"
#include "sensor_instruction_common.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace sensor {

TouchSensorInstruction::TouchSensorInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::ReadTouch)) {}

ExecutionResult TouchSensorInstruction::execute(InstructionContext& ctx) {
    if (ctx.context().operandStack().empty()) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            1,
            "TOUCH_SENSOR: no port on operand stack",
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
            "TOUCH_SENSOR: port must be integer",
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
    request.setApiId(ApiId::READ_TOUCH);
    request.addParameter(RuntimeValue(port));

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

bool TouchSensorInstruction::validate(InstructionContext& ctx) {
    return !ctx.context().operandStack().empty();
}

std::string TouchSensorInstruction::name() const {
    return "READ_TOUCH";
}

uint32_t TouchSensorInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory TouchSensorInstruction::category() const {
    return InstructionCategory::Sensor;
}

Semantic TouchSensorInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace sensor
} // namespace execution
} // namespace robot