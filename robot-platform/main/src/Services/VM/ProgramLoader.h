#pragma once

#include "Program.h"

class ProgramLoader
{
public:
    static bool LoadFromGenerated(Program& program);
    static bool LoadFromArray(Program& program, const Instruction* instructions, uint16_t size);

    // --- Extended interfaces (placeholders) ---
    static bool LoadBinary(Program& program, const uint8_t* data, uint16_t size);
    static bool LoadFlash(Program& program, uint16_t address);
    static bool LoadUART(Program& program);
};