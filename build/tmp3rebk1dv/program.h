/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 3000, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::CompareLT, 1, 0, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 23, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 4, 0, 0, 0),
    Instruction(Opcode::Store, 4, 3, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::Neg, 5, 0, 6, 0),
    Instruction(Opcode::CompareEQ, 3, 6, 7, 0),
    Instruction(Opcode::JumpIfFalse, 7, 14, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::LoadConst, 9, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 8, 9, 0, 0),
    Instruction(Opcode::Jump, 0, 17, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1, 0, 0),
    Instruction(Opcode::LoadConst, 11, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 10, 11, 0, 0),
    Instruction(Opcode::LoadConst, 12, 200, 0, 0),
    Instruction(Opcode::Wait, 12, 0, 0, 0),
    Instruction(Opcode::LoadConst, 13, 1, 0, 0),
    Instruction(Opcode::Add, 1, 13, 2, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 2, 0, 0),
};

const uint16_t generatedProgramSize = 23;
