/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 0, 30, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::CompareLT, 1, 0, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 19, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 4, 0, 0, 0),
    Instruction(Opcode::Store, 4, 3, 0, 0),
    Instruction(Opcode::LoadConst, 5, 0, 0, 0),
    Instruction(Opcode::CompareGE, 3, 5, 6, 0),
    Instruction(Opcode::JumpIfFalse, 6, 12, 0, 0),
    Instruction(Opcode::Nop, 0, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 13, 0, 0),
    Instruction(Opcode::Nop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 7, 200, 0, 0),
    Instruction(Opcode::Wait, 7, 0, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::Add, 1, 8, 2, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 3, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 20;
