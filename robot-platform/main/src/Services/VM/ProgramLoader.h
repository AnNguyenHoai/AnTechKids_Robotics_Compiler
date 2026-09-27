#pragma once

#include "Program.h"

class ProgramLoader
{
public:
    static bool LoadFromGenerated(Program& program);
    static bool LoadFromArray(Program& program, const Instruction* instructions, uint16_t size);

    // Deterministic identity of the generated program compiled into firmware.
    // Hash is FNV-1a over opcode/p1..p4 values, not raw struct bytes, so it is
    // stable across padding/alignment differences.
    static uint16_t GeneratedProgramSize();
    static uint32_t GeneratedProgramHash();

    // --- Extended interfaces (placeholders) ---
    static bool LoadBinary(Program& program, const uint8_t* data, uint16_t size);
    static bool LoadFlash(Program& program, uint16_t address);
    static bool LoadUART(Program& program);
};