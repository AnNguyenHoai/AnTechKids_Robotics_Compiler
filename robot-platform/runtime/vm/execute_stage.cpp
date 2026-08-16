#include "execute_stage.h"

namespace robot {
namespace execution {

ExecuteStage::ExecuteStage(InstructionDispatcher& dispatcher, InstructionContext& ctx)
    : m_dispatcher(dispatcher), m_ctx(ctx) {}

ExecutionResult ExecuteStage::execute(const ProgramInstruction& instruction) {
    // Dispatch the instruction
    return m_dispatcher.dispatch(m_ctx, instruction.opcode);
}

} // namespace execution
} // namespace robot