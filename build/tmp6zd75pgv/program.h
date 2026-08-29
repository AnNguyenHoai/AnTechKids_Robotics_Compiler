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
    Instruction(Opcode::JumpIfFalse, 2, 22, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 3, 4, 0, 0),
    Instruction(Opcode::LoadConst, 5, 2, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 5, 6, 0, 0),
    Instruction(Opcode::LoadConst, 7, 500, 0, 0),
    Instruction(Opcode::Wait, 7, 0, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::LoadConst, 9, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 8, 9, 0, 0),
    Instruction(Opcode::LoadConst, 10, 2, 0, 0),
    Instruction(Opcode::LoadConst, 11, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 10, 11, 0, 0),
    Instruction(Opcode::LoadConst, 12, 1, 0, 0),
    Instruction(Opcode::Add, 1, 12, 2, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 2, 0, 0),
};

const uint16_t generatedProgramSize = 22;
