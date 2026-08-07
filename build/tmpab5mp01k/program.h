/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 1, 2, 0, 0),
    Instruction(Opcode::ReadLine, 1, 2, 0, 0),
    Instruction(Opcode::Store, 2, 0, 0, 0),
    Instruction(Opcode::JumpIfFalse, 0, 10, 0, 0),
    Instruction(Opcode::LoadConst, 3, 80, 0, 0),
    Instruction(Opcode::Forward, 3, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1000, 0, 0),
    Instruction(Opcode::Wait, 4, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 15, 0, 0),
    Instruction(Opcode::LoadConst, 5, 80, 0, 0),
    Instruction(Opcode::Backward, 5, 0, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1000, 0, 0),
    Instruction(Opcode::Wait, 6, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 15;
