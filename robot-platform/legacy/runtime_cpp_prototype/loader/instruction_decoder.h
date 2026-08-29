#pragma once

#include "bytecode_format.h"
#include "execution_types.h"
#include <vector>
#include <cstdint>
#include <optional>

namespace robot {
namespace execution {

struct DecodedInstruction {
    uint32_t opcode;
    std::vector<uint32_t> operands;
    size_t byteSize; // size in bytes
};

class InstructionDecoder {
public:
    // Decode a single instruction from bytecode.
    static std::optional<DecodedInstruction> decode(const BytecodeInstruction& rawInstr);

    // Decode all instructions from a reader.
    static std::vector<DecodedInstruction> decodeAll(const std::vector<BytecodeInstruction>& rawInstructions);

    // Validate opcode (check if it's known)
    static bool isOpcodeValid(uint32_t opcode);
};

} // namespace execution
} // namespace robot