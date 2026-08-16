/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 1, 80, 0, 0),
    Instruction(Opcode::Forward, 1, 0, 0, 0),
    Instruction(Opcode::LoadConst, 0, 1, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 3, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 25, 0, 0),
    Instruction(Opcode::CompareLT, 3, 4, 5, 0),
    Instruction(Opcode::JumpIfFalse, 5, 13, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::CompareEQ, 0, 6, 7, 0),
    Instruction(Opcode::JumpIfFalse, 7, 13, 0, 0),
    Instruction(Opcode::LoadConst, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 14, 0, 0),
    Instruction(Opcode::LoadConst, 2, 0, 0, 0),
    Instruction(Opcode::JumpIfFalse, 2, 23, 0, 0),
    Instruction(Opcode::LoadConst, 8, 70, 0, 0),
    Instruction(Opcode::TurnLeft, 8, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 600, 0, 0),
    Instruction(Opcode::Wait, 9, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1, 0, 0),
    Instruction(Opcode::LoadConst, 11, 80, 0, 0),
    Instruction(Opcode::Forward, 11, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 4, 0, 0),
};

const uint16_t generatedProgramSize = 24;
