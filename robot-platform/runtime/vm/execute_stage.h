#pragma once

#include "instruction/instruction_context.h"
#include "dispatcher/instruction_dispatcher.h"
#include "execution_result.h"
#include <cstdint>

namespace robot {
namespace execution {

class ExecuteStage {
public:
    ExecuteStage(InstructionDispatcher& dispatcher, InstructionContext& ctx);

    ExecutionResult execute(const ProgramInstruction& instruction);

private:
    InstructionDispatcher& m_dispatcher;
    InstructionContext& m_ctx;
};

} // namespace execution
} // namespace robot