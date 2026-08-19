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
    Instruction(Opcode::LoadConst, 1, 500, 0, 0),
    Instruction(Opcode::Wait, 1, 0, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 2, 500, 0, 0),
    Instruction(Opcode::Wait, 2, 0, 0, 0),
    Instruction(Opcode::ReadUltrasonic, 4, 0, 0, 0),
    Instruction(Opcode::Store, 4, 3, 0, 0),
    Instruction(Opcode::LoadConst, 5, 0, 0, 0),
    Instruction(Opcode::CompareGT, 3, 5, 6, 0),
    Instruction(Opcode::JumpIfFalse, 6, 16, 0, 0),
    Instruction(Opcode::LoadConst, 7, 1, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 7, 8, 0, 0),
    Instruction(Opcode::Jump, 0, 19, 0, 0),
    Instruction(Opcode::LoadConst, 9, 1, 0, 0),
    Instruction(Opcode::LoadConst, 10, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 9, 10, 0, 0),
    Instruction(Opcode::LoadConst, 11, 500, 0, 0),
    Instruction(Opcode::Wait, 11, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 22;
