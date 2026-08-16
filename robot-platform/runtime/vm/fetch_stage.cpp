#include "fetch_stage.h"

namespace robot {
namespace execution {

FetchStage::FetchStage() : m_error() {}

std::optional<ProgramInstruction> FetchStage::fetch(const Program& program, ExecutionContext& context) {
    m_error.clear();

    if (!context.programCounter().isValid()) {
        m_error = "Program counter not set";
        return std::nullopt;
    }

    uint32_t pc = context.programCounter().current();
    if (pc >= program.instructionCount()) {
        m_error = "Program counter out of bounds: " + std::to_string(pc);
        return std::nullopt;
    }

    return program.getInstruction(pc);
}

std::string FetchStage::lastError() const {
    return m_error;
}

} // namespace execution
} // namespace robot