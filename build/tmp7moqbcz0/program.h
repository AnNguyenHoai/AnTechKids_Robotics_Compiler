/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 10, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::CompareLT, 1, 0, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 26, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::SetMp3Play, 3, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 4, 5, 0, 0),
    Instruction(Opcode::LoadConst, 6, 2, 0, 0),
    Instruction(Opcode::LoadConst, 7, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 6, 7, 0, 0),
    Instruction(Opcode::LoadConst, 8, 3, 0, 0),
    Instruction(Opcode::Wait, 8, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 0, 0, 0),
    Instruction(Opcode::SetMp3Play, 9, 0, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1, 0, 0),
    Instruction(Opcode::LoadConst, 11, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 10, 11, 0, 0),
    Instruction(Opcode::LoadConst, 12, 2, 0, 0),
    Instruction(Opcode::LoadConst, 13, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 12, 13, 0, 0),
    Instruction(Opcode::LoadConst, 14, 1, 0, 0),
    Instruction(Opcode::Add, 1, 14, 2, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 2, 0, 0),
    Instruction(Opcode::LoadConst, 15, 3, 0, 0),
    Instruction(Opcode::Wait, 15, 0, 0, 0),
};

const uint16_t generatedProgramSize = 28;
