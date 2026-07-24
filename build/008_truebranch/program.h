/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 80, 0),
    Instruction(Opcode::LoadConst, 1, 50, 0),
    Instruction(Opcode::CompareGT, 0, 1, 2),
    Instruction(Opcode::JumpIfFalse, 2, 10, 0),
    Instruction(Opcode::LoadConst, 3, 50, 0),
    Instruction(Opcode::Forward, 3, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1000, 0),
    Instruction(Opcode::Wait, 4, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 15, 0),
    Instruction(Opcode::LoadConst, 5, 50, 0),
    Instruction(Opcode::Backward, 5, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1000, 0),
    Instruction(Opcode::Wait, 6, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0),
};

const uint16_t generatedProgramSize = 15;
