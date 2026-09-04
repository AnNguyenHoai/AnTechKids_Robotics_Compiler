#pragma once

#include "../loader/program.h"
#include "execution_context.h"
#include "execution_result.h"
#include <optional>

namespace robot {
namespace execution {

class FetchStage {
public:
    FetchStage();

    // Fetch instruction at current program counter
    std::optional<ProgramInstruction> fetch(const Program& program, ExecutionContext& context);

    // Get last error
    std::string lastError() const;

private:
    std::string m_error;
};

} // namespace execution
} // namespace robot