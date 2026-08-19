/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 80, 0, 0),
    Instruction(Opcode::Forward, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 1, 150, 0, 0),
    Instruction(Opcode::Wait, 1, 0, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 3, 0, 0, 0),
    Instruction(Opcode::Store, 3, 2, 0, 0),
    Instruction(Opcode::LoadConst, 4, 0, 0, 0),
    Instruction(Opcode::CompareGT, 2, 4, 5, 0),
    Instruction(Opcode::JumpIfFalse, 5, 13, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::LoadConst, 7, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 6, 7, 0, 0),
    Instruction(Opcode::Jump, 0, 16, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::LoadConst, 9, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 8, 9, 0, 0),
    Instruction(Opcode::LoadConst, 10, 3000, 0, 0),
    Instruction(Opcode::Wait, 10, 0, 0, 0),
};

const uint16_t generatedProgramSize = 18;
