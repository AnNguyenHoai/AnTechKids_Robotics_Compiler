/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 80, 0, 0),
    Instruction(Opcode::LoadConst, 1, 100, 0, 0),
    Instruction(Opcode::SetMotorSpeed, 0, 1, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 2, 0, 0, 0),
    Instruction(Opcode::LoadConst, 3, 30, 0, 0),
    Instruction(Opcode::CompareLT, 2, 3, 4, 0),
    Instruction(Opcode::JumpIfFalse, 4, 12, 0, 0),
    Instruction(Opcode::LoadConst, 5, 80, 0, 0),
    Instruction(Opcode::Backward, 5, 0, 0, 0),
    Instruction(Opcode::LoadConst, 6, 3000, 0, 0),
    Instruction(Opcode::Wait, 6, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 12;
