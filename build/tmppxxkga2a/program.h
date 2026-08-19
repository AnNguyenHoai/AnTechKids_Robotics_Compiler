/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 50, 0, 0),
    Instruction(Opcode::Forward, 0, 0, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 2, 0, 0, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::LoadConst, 3, 0, 0, 0),
    Instruction(Opcode::CompareGT, 1, 3, 4, 0),
    Instruction(Opcode::JumpIfFalse, 4, 11, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 5, 6, 0, 0),
    Instruction(Opcode::Jump, 0, 14, 0, 0),
    Instruction(Opcode::LoadConst, 7, 1, 0, 0),
    Instruction(Opcode::LoadConst, 8, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 7, 8, 0, 0),
    Instruction(Opcode::LoadConst, 9, 200, 0, 0),
    Instruction(Opcode::Wait, 9, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 17;
