#include "unknown_instruction_handler.h"
#include <string>

namespace robot {
namespace execution {

UnknownInstructionHandler::UnknownInstructionHandler(uint32_t opcode) : m_opcode(opcode) {}

ExecutionResult UnknownInstructionHandler::execute(InstructionContext& ctx) {
    (void)ctx;
    return ExecutionResult(
        ExecutionStatus::Failure,
        1,
        "Unknown instruction opcode: " + std::to_string(m_opcode),
        ctx.context().programCounter().current(),
        ExecutionLayer::Dispatcher,
        m_opcode
    );
}

bool UnknownInstructionHandler::validate(InstructionContext& ctx) {
    (void)ctx;
    return false;
}

std::string UnknownInstructionHandler::name() const {
    return "UnknownInstruction";
}

uint32_t UnknownInstructionHandler::opcode() const {
    return m_opcode;
}

InstructionCategory UnknownInstructionHandler::category() const {
    return InstructionCategory::Unknown;
}

Semantic UnknownInstructionHandler::semantic() const {
    return Semantic::Unknown;
}

} // namespace execution
} // namespace robot