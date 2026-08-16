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
    Instruction(Opcode::CompareLT, 0, 2, 3, 0),
    Instruction(Opcode::JumpIfFalse, 3, 11, 0, 0),
    Instruction(Opcode::LoadConst, 4, 70, 0, 0),
    Instruction(Opcode::TurnLeft, 4, 0, 0, 0),
    Instruction(Opcode::LoadConst, 5, 500, 0, 0),
    Instruction(Opcode::Wait, 5, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 13, 0, 0),
    Instruction(Opcode::LoadConst, 6, 100, 0, 0),
    Instruction(Opcode::Forward, 6, 0, 0, 0),
    Instruction(Opcode::LoadConst, 7, 100, 0, 0),
    Instruction(Opcode::Wait, 7, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 16;
