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
    Instruction(Opcode::LoadConst, 2, 20, 0, 0),
    Instruction(Opcode::CompareGT, 0, 2, 3, 0),
    Instruction(Opcode::JumpIfFalse, 3, 10, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::LoadConst, 5, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 4, 5, 0, 0),
    Instruction(Opcode::Jump, 0, 23, 0, 0),
    Instruction(Opcode::LoadConst, 6, 0, 0, 0),
    Instruction(Opcode::CompareGT, 0, 6, 7, 0),
    Instruction(Opcode::JumpIfFalse, 7, 19, 0, 0),
    Instruction(Opcode::LoadConst, 8, 80, 0, 0),
    Instruction(Opcode::Forward, 8, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 1, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 9, 10, 0, 0),
    Instruction(Opcode::Jump, 0, 23, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 11, 1, 0, 0),
    Instruction(Opcode::LoadConst, 12, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 11, 12, 0, 0),
    Instruction(Opcode::LoadConst, 13, 200, 0, 0),
    Instruction(Opcode::Wait, 13, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 26;
