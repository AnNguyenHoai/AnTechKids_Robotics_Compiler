#include "ProgramLoader.h"
#include "../Application/generated_program.h"

bool ProgramLoader::LoadFromGenerated(Program& program)
{
    program.Clear();
    for (uint16_t i = 0; i < generatedProgramSize; i++)
    {
        if (!program.AddInstruction(generatedProgram[i]))
        {
            return false;
        }
    }
    return true;
}

bool ProgramLoader::LoadFromArray(Program& program, const Instruction* instructions, uint16_t size)
{
    program.Clear();
    for (uint16_t i = 0; i < size; i++)
    {
        if (!program.AddInstruction(instructions[i]))
        {
            return false;
        }
    }
    return true;
}