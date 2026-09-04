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
    Instruction(Opcode::LoadConst, 2, 1, 0, 0),
    Instruction(Opcode::Neg, 2, 0, 3, 0),
    Instruction(Opcode::CompareEQ, 0, 3, 4, 0),
    Instruction(Opcode::JumpIfFalse, 4, 11, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::LoadConst, 6, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 5, 6, 0, 0),
    Instruction(Opcode::Jump, 0, 27, 0, 0),
    Instruction(Opcode::LoadConst, 7, 20, 0, 0),
    Instruction(Opcode::CompareLT, 0, 7, 8, 0),
    Instruction(Opcode::JumpIfFalse, 8, 19, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 2, 0, 0),
    Instruction(Opcode::LoadConst, 10, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 9, 10, 0, 0),
    Instruction(Opcode::Jump, 0, 27, 0, 0),
    Instruction(Opcode::LoadConst, 11, 80, 0, 0),
    Instruction(Opcode::Forward, 11, 0, 0, 0),
    Instruction(Opcode::LoadConst, 12, 1, 0, 0),
    Instruction(Opcode::LoadConst, 13, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 12, 13, 0, 0),
    Instruction(Opcode::LoadConst, 14, 2, 0, 0),
    Instruction(Opcode::LoadConst, 15, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 14, 15, 0, 0),
    Instruction(Opcode::LoadConst, 16, 200, 0, 0),
    Instruction(Opcode::Wait, 16, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 30;
