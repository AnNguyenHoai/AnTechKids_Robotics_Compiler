/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, False, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 3, 0, 0, 0),
    Instruction(Opcode::Store, 3, 2, 0, 0),
    Instruction(Opcode::LoadConst, 4, 0, 0, 0),
    Instruction(Opcode::CompareLT, 2, 4, 5, 0),
    Instruction(Opcode::JumpIfFalse, 5, 13, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::LoadConst, 7, 5, 0, 0),
    Instruction(Opcode::CompareGE, 1, 7, 8, 0),
    Instruction(Opcode::JumpIfFalse, 8, 12, 0, 0),
    Instruction(Opcode::LoadConst, 0, True, 0, 0),
    Instruction(Opcode::Jump, 0, 20, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 20, 0, 0),
    Instruction(Opcode::CompareLT, 2, 9, 10, 0),
    Instruction(Opcode::JumpIfFalse, 10, 19, 0, 0),
    Instruction(Opcode::LoadConst, 0, True, 0, 0),
    Instruction(Opcode::Jump, 0, 20, 0, 0),
    Instruction(Opcode::LoadConst, 0, False, 0, 0),
    Instruction(Opcode::JumpIfFalse, 0, 26, 0, 0),
    Instruction(Opcode::LoadConst, 11, 1, 0, 0),
    Instruction(Opcode::LoadConst, 12, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 11, 12, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 31, 0, 0),
    Instruction(Opcode::LoadConst, 13, 80, 0, 0),
    Instruction(Opcode::Forward, 13, 0, 0, 0),
    Instruction(Opcode::LoadConst, 14, 1, 0, 0),
    Instruction(Opcode::LoadConst, 15, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 14, 15, 0, 0),
    Instruction(Opcode::LoadConst, 16, 100, 0, 0),
    Instruction(Opcode::Wait, 16, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 2, 0, 0),
};

const uint16_t generatedProgramSize = 34;
