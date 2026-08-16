#include "color_sensor_instruction.h"
#include "robot_api_dispatcher.h"
#include "robot_api_request.h"
#include "execution_context.h"
#include "runtime_value.h"

namespace robot {
namespace execution {
namespace sensor {

ColorSensorInstruction::ColorSensorInstruction()
    : m_opcode(static_cast<uint32_t>(Opcode::ReadColor)) {}

ExecutionResult ColorSensorInstruction::execute(InstructionContext& ctx) {
    RobotApiRequest request;
    request.setApiId(ApiId::READ_COLOR);

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

bool ColorSensorInstruction::validate(InstructionContext& ctx) {
    return true;
}

std::string ColorSensorInstruction::name() const {
    return "READ_COLOR";
}

uint32_t ColorSensorInstruction::opcode() const {
    return m_opcode;
}

InstructionCategory ColorSensorInstruction::category() const {
    return InstructionCategory::Sensor;
}

Semantic ColorSensorInstruction::semantic() const {
    return Semantic::Native;
}

} // namespace sensor
} // namespace execution
} // namespace robot