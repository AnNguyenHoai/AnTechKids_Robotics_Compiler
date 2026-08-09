/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 45, 0, 0),
    Instruction(Opcode::TurnRight, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 1, 500, 0, 0),
    Instruction(Opcode::Wait, 1, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 2, 50, 0, 0),
    Instruction(Opcode::LoadConst, 3, 50, 0, 0),
    Instruction(Opcode::SetMotorSpeed, 2, 3, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 4, 0, 0, 0),
    Instruction(Opcode::LoadConst, 5, 30, 0, 0),
    Instruction(Opcode::CompareLT, 4, 5, 6, 0),
    Instruction(Opcode::JumpIfFalse, 6, 22, 0, 0),
    Instruction(Opcode::LoadConst, 7, 50, 0, 0),
    Instruction(Opcode::TurnLeft, 7, 0, 0, 0),
    Instruction(Opcode::LoadConst, 8, 500, 0, 0),
    Instruction(Opcode::Wait, 8, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 50, 0, 0),
    Instruction(Opcode::Forward, 9, 0, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1000, 0, 0),
    Instruction(Opcode::Wait, 10, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 22;
