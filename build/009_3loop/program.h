/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 3, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0),
    Instruction(Opcode::CompareLT, 1, 0, 2),
    Instruction(Opcode::JumpIfFalse, 2, 13, 0),
    Instruction(Opcode::LoadConst, 3, 50, 0),
    Instruction(Opcode::Forward, 3, 0, 0),
    Instruction(Opcode::LoadConst, 4, 500, 0),
    Instruction(Opcode::Wait, 4, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0),
    Instruction(Opcode::Add, 1, 5, 2),
    Instruction(Opcode::Store, 2, 1, 0),
    Instruction(Opcode::Jump, 0, 2, 0),
};

const uint16_t generatedProgramSize = 13;
