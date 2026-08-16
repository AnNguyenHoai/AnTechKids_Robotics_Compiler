#pragma once

#include <cstdint>

namespace robot {
namespace execution {

// Bytecode format constants
constexpr uint32_t MAGIC_NUMBER = 0x52424F54; // "RBOT"
constexpr uint8_t BYTECODE_VERSION_MAJOR = 1;
constexpr uint8_t BYTECODE_VERSION_MINOR = 0;

// Header structure (as it appears in bytecode)
#pragma pack(push, 1)
struct BytecodeHeader {
    uint32_t magic;
    uint8_t versionMajor;
    uint8_t versionMinor;
    uint32_t constantPoolSize;
    uint32_t instructionCount;
    uint32_t entryPoint; // instruction index
    uint32_t checksum;   // placeholder
};
#pragma pack(pop)

// Instruction structure (stored in bytecode)
#pragma pack(push, 1)
struct BytecodeInstruction {
    uint32_t opcode;
    uint8_t operandCount;
    uint32_t operands[4]; // up to 4 operands for simplicity
};
#pragma pack(pop)

} // namespace execution
} // namespace robot