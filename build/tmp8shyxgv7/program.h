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
    Instruction(Opcode::LoadConst, 2, 30, 0, 0),
    Instruction(Opcode::CompareLT, 0, 2, 3, 0),
    Instruction(Opcode::JumpIfFalse, 3, 7, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 10, 0, 0),
    Instruction(Opcode::LoadConst, 4, 80, 0, 0),
    Instruction(Opcode::LoadConst, 5, 90, 0, 0),
    Instruction(Opcode::SetMotorSpeed, 4, 5, 0, 0),
    Instruction(Opcode::LoadConst, 6, 100, 0, 0),
    Instruction(Opcode::Wait, 6, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 13;
