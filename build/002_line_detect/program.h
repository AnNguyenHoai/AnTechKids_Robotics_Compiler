/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 1, 0),
    Instruction(Opcode::ReadLine, 0, 1, 0),
    Instruction(Opcode::LoadConst, 2, 1, 0),
    Instruction(Opcode::CompareEQ, 1, 2, 3),
    Instruction(Opcode::JumpIfFalse, 3, 10, 0),
    Instruction(Opcode::LoadConst, 4, 100, 0),
    Instruction(Opcode::Backward, 4, 0, 0),
    Instruction(Opcode::LoadConst, 5, 100, 0),
    Instruction(Opcode::Wait, 5, 0, 0),
    Instruction(Opcode::Jump, 0, 11, 0),
    Instruction(Opcode::Stop, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0),
};

const uint16_t generatedProgramSize = 12;
