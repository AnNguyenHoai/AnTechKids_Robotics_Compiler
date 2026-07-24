#include "ProgramLoader.h"
#include "../../Application/generated_program.h"

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

bool ProgramLoader::LoadBinary(Program& program, const uint8_t* data, uint16_t size)
{
    // TODO: parse binary format and fill program
    // Placeholder: not implemented
    (void)program;
    (void)data;
    (void)size;
    return false;
}

bool ProgramLoader::LoadFlash(Program& program, uint16_t address)
{
    // TODO: read from flash memory
    (void)program;
    (void)address;
    return false;
}

bool ProgramLoader::LoadUART(Program& program)
{
    // TODO: receive program via UART
    (void)program;
    return false;
}