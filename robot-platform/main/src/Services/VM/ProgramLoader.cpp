#include "ProgramLoader.h"
#include "../../Application/generated_program.h"

namespace {
uint32_t fnv1aByte(uint32_t hash, uint8_t value) {
    hash ^= value;
    return hash * 16777619UL;
}

uint32_t fnv1aU32(uint32_t hash, uint32_t value) {
    hash = fnv1aByte(hash, static_cast<uint8_t>(value & 0xFFu));
    hash = fnv1aByte(hash, static_cast<uint8_t>((value >> 8) & 0xFFu));
    hash = fnv1aByte(hash, static_cast<uint8_t>((value >> 16) & 0xFFu));
    hash = fnv1aByte(hash, static_cast<uint8_t>((value >> 24) & 0xFFu));
    return hash;
}
}

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

uint16_t ProgramLoader::GeneratedProgramSize()
{
    return generatedProgramSize;
}

uint32_t ProgramLoader::GeneratedProgramHash()
{
    uint32_t hash = 2166136261UL;
    for (uint16_t i = 0; i < generatedProgramSize; ++i) {
        const Instruction& instruction = generatedProgram[i];
        hash = fnv1aByte(hash, static_cast<uint8_t>(instruction.opcode));
        hash = fnv1aU32(hash, static_cast<uint32_t>(instruction.p1));
        hash = fnv1aU32(hash, static_cast<uint32_t>(instruction.p2));
        hash = fnv1aU32(hash, static_cast<uint32_t>(instruction.p3));
        hash = fnv1aU32(hash, static_cast<uint32_t>(instruction.p4));
    }
    return hash;
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