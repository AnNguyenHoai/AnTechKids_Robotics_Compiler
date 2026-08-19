/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 0, 3000, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::CompareLT, 1, 0, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 31, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 4, 0, 0, 0),
    Instruction(Opcode::Store, 4, 3, 0, 0),
    Instruction(Opcode::LoadConst, 5, 0, 0, 0),
    Instruction(Opcode::CompareGT, 3, 5, 6, 0),
    Instruction(Opcode::JumpIfFalse, 6, 14, 0, 0),
    Instruction(Opcode::LoadConst, 7, 1, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 7, 8, 0, 0),
    Instruction(Opcode::Jump, 0, 25, 0, 0),
    Instruction(Opcode::LoadConst, 9, 1, 0, 0),
    Instruction(Opcode::Neg, 9, 0, 10, 0),
    Instruction(Opcode::CompareEQ, 3, 10, 11, 0),
    Instruction(Opcode::JumpIfFalse, 11, 22, 0, 0),
    Instruction(Opcode::LoadConst, 12, 1, 0, 0),
    Instruction(Opcode::LoadConst, 13, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 12, 13, 0, 0),
    Instruction(Opcode::Jump, 0, 25, 0, 0),
    Instruction(Opcode::LoadConst, 14, 1, 0, 0),
    Instruction(Opcode::LoadConst, 15, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 14, 15, 0, 0),
    Instruction(Opcode::LoadConst, 16, 200, 0, 0),
    Instruction(Opcode::Wait, 16, 0, 0, 0),
    Instruction(Opcode::LoadConst, 17, 1, 0, 0),
    Instruction(Opcode::Add, 1, 17, 2, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 3, 0, 0),
};

const uint16_t generatedProgramSize = 31;
