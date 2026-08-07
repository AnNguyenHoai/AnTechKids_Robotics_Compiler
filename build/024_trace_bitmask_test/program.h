/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 1, 20, 0, 0),
    Instruction(Opcode::CompareLT, 0, 1, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 21, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::GetTraceRaw, 4, 0, 5, 0),
    Instruction(Opcode::Store, 5, 3, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::CompareEQ, 3, 6, 7, 0),
    Instruction(Opcode::JumpIfFalse, 7, 14, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::LoadConst, 9, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 8, 9, 0, 0),
    Instruction(Opcode::Jump, 0, 17, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1, 0, 0),
    Instruction(Opcode::LoadConst, 11, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 10, 11, 0, 0),
    Instruction(Opcode::LoadConst, 12, 50, 0, 0),
    Instruction(Opcode::Wait, 12, 0, 0, 0),
    Instruction(Opcode::LoadConst, 13, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 1, 0, 0),
};

const uint16_t generatedProgramSize = 21;
