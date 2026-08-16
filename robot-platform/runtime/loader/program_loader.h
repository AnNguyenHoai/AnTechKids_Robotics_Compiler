#pragma once

#include "program.h"
#include "execution_result.h"
#include <vector>
#include <cstdint>

namespace robot {
namespace execution {

/**
 * ProgramLoader – transforms bytecode into a Runtime Program.
 *
 * It owns the loading pipeline: read, decode, validate, build Program.
 * No execution logic; pure transformation.
 */
class ProgramLoader {
public:
    ProgramLoader() = default;

    // Main entry point
    ExecutionResult load(const uint8_t* bytecode, size_t size, Program& outProgram);

    // Convenience overload using vector
    ExecutionResult load(const std::vector<uint8_t>& bytecode, Program& outProgram);

private:
    ExecutionResult validateHeader(const BytecodeHeader& header);
    ExecutionResult buildProgram(Program& program);
};

} // namespace execution
} // namespace robot