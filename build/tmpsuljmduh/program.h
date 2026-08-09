/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 1, 50, 0, 0),
    Instruction(Opcode::Forward, 1, 0, 0, 0),
    Instruction(Opcode::LoadConst, 0, 1, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 3, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 15, 0, 0),
    Instruction(Opcode::CompareLT, 3, 4, 5, 0),
    Instruction(Opcode::JumpIfFalse, 5, 13, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::CompareEQ, 0, 6, 7, 0),
    Instruction(Opcode::JumpIfFalse, 7, 13, 0, 0),
    Instruction(Opcode::LoadConst, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 14, 0, 0),
    Instruction(Opcode::LoadConst, 2, 0, 0, 0),
    Instruction(Opcode::JumpIfFalse, 2, 23, 0, 0),
    Instruction(Opcode::LoadConst, 8, 55, 0, 0),
    Instruction(Opcode::TurnLeft, 8, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 400, 0, 0),
    Instruction(Opcode::Wait, 9, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1, 0, 0),
    Instruction(Opcode::LoadConst, 11, 50, 0, 0),
    Instruction(Opcode::Forward, 11, 0, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 13, 0, 0, 0),
    Instruction(Opcode::LoadConst, 14, 15, 0, 0),
    Instruction(Opcode::CompareLT, 13, 14, 15, 0),
    Instruction(Opcode::JumpIfFalse, 15, 32, 0, 0),
    Instruction(Opcode::LoadConst, 16, 2, 0, 0),
    Instruction(Opcode::CompareEQ, 0, 16, 17, 0),
    Instruction(Opcode::JumpIfFalse, 17, 32, 0, 0),
    Instruction(Opcode::LoadConst, 12, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 33, 0, 0),
    Instruction(Opcode::LoadConst, 12, 0, 0, 0),
    Instruction(Opcode::JumpIfFalse, 12, 45, 0, 0),
    Instruction(Opcode::LoadConst, 18, 55, 0, 0),
    Instruction(Opcode::TurnRight, 18, 0, 0, 0),
    Instruction(Opcode::LoadConst, 19, 400, 0, 0),
    Instruction(Opcode::Wait, 19, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 20, 50, 0, 0),
    Instruction(Opcode::Forward, 20, 0, 0, 0),
    Instruction(Opcode::LoadConst, 21, 1000, 0, 0),
    Instruction(Opcode::Wait, 21, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 4, 0, 0),
};

const uint16_t generatedProgramSize = 46;
