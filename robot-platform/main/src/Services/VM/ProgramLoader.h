#pragma once

#include "Program.h"

class ProgramLoader
{
public:
    static bool LoadFromGenerated(Program& program);
    static bool LoadFromArray(Program& program, const Instruction* instructions, uint16_t size);
};