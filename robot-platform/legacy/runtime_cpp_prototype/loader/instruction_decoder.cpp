#include "instruction_decoder.h"
#include <unordered_set>

namespace robot {
namespace execution {

static const std::unordered_set<uint32_t> VALID_OPCODES = {
    static_cast<uint32_t>(Opcode::NOP),
    static_cast<uint32_t>(Opcode::END),
    static_cast<uint32_t>(Opcode::WAIT),
    static_cast<uint32_t>(Opcode::JUMP),
    static_cast<uint32_t>(Opcode::JUMP_IF),
    static_cast<uint32_t>(Opcode::LOAD_CONST),
    static_cast<uint32_t>(Opcode::STORE),
    static_cast<uint32_t>(Opcode::LOAD),
    static_cast<uint32_t>(Opcode::RETURN),
    // Future opcodes will be added here
};

std::optional<DecodedInstruction> InstructionDecoder::decode(const BytecodeInstruction& rawInstr) {
    if (!isOpcodeValid(rawInstr.opcode)) {
        return std::nullopt;
    }

    DecodedInstruction decoded;
    decoded.opcode = rawInstr.opcode;
    decoded.byteSize = sizeof(BytecodeInstruction);

    // Copy operands
    for (uint8_t i = 0; i < rawInstr.operandCount && i < 4; ++i) {
        decoded.operands.push_back(rawInstr.operands[i]);
    }

    return decoded;
}

std::vector<DecodedInstruction> InstructionDecoder::decodeAll(
    const std::vector<BytecodeInstruction>& rawInstructions) {
    std::vector<DecodedInstruction> result;
    for (const auto& raw : rawInstructions) {
        auto decoded = decode(raw);
        if (decoded) {
            result.push_back(*decoded);
        }
    }
    return result;
}

bool InstructionDecoder::isOpcodeValid(uint32_t opcode) {
    return VALID_OPCODES.find(opcode) != VALID_OPCODES.end();
}

} // namespace execution
} // namespace robot