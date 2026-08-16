/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::ReadUltrasonic, 1, 0, 0, 0),
    Instruction(Opcode::Store, 1, 0, 0, 0),
    Instruction(Opcode::LoadConst, 3, 0, 0, 0),
    Instruction(Opcode::CompareGE, 0, 3, 4, 0),
    Instruction(Opcode::JumpIfFalse, 4, 10, 0, 0),
    Instruction(Opcode::LoadConst, 5, 20, 0, 0),
    Instruction(Opcode::CompareLT, 0, 5, 6, 0),
    Instruction(Opcode::JumpIfFalse, 6, 10, 0, 0),
    Instruction(Opcode::LoadConst, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 11, 0, 0),
    Instruction(Opcode::LoadConst, 2, 0, 0, 0),
    Instruction(Opcode::JumpIfFalse, 2, 18, 0, 0),
    Instruction(Opcode::LoadConst, 7, 1, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 7, 8, 0, 0),
    Instruction(Opcode::LoadConst, 9, 0, 0, 0),
    Instruction(Opcode::Forward, 9, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 23, 0, 0),
    Instruction(Opcode::LoadConst, 10, 80, 0, 0),
    Instruction(Opcode::Forward, 10, 0, 0, 0),
    Instruction(Opcode::LoadConst, 11, 1, 0, 0),
    Instruction(Opcode::LoadConst, 12, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 11, 12, 0, 0),
    Instruction(Opcode::LoadConst, 13, 100, 0, 0),
    Instruction(Opcode::Wait, 13, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 26;
