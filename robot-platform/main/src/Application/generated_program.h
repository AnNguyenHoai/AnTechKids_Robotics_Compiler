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
    Instruction(Opcode::ReadUltrasonic, 1, 0, 0, 0),
    Instruction(Opcode::LoadConst, 2, 15, 0, 0),
    Instruction(Opcode::CompareLT, 1, 2, 3, 0),
    Instruction(Opcode::JumpIfFalse, 3, 40, 0, 0),
    Instruction(Opcode::Stop, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::SetMp3Play, 4, 0, 0, 0),
    Instruction(Opcode::LoadConst, 5, 2, 0, 0),
    Instruction(Opcode::LoadConst, 6, 2, 0, 0),
    Instruction(Opcode::Set3CLed, 5, 6, 0, 0),
    Instruction(Opcode::LoadConst, 7, 3, 0, 0),
    Instruction(Opcode::LoadConst, 8, 3, 0, 0),
    Instruction(Opcode::Set3CLed, 7, 8, 0, 0),
    Instruction(Opcode::LoadConst, 9, 4, 0, 0),
    Instruction(Opcode::LoadConst, 10, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 9, 10, 0, 0),
    Instruction(Opcode::LoadConst, 11, 1000, 0, 0),
    Instruction(Opcode::Wait, 11, 0, 0, 0),
    Instruction(Opcode::LoadConst, 12, 2, 0, 0),
    Instruction(Opcode::LoadConst, 13, 5, 0, 0),
    Instruction(Opcode::Set3CLed, 12, 13, 0, 0),
    Instruction(Opcode::LoadConst, 14, 3, 0, 0),
    Instruction(Opcode::LoadConst, 15, 6, 0, 0),
    Instruction(Opcode::Set3CLed, 14, 15, 0, 0),
    Instruction(Opcode::LoadConst, 16, 4, 0, 0),
    Instruction(Opcode::LoadConst, 17, 4, 0, 0),
    Instruction(Opcode::Set3CLed, 16, 17, 0, 0),
    Instruction(Opcode::LoadConst, 18, 1000, 0, 0),
    Instruction(Opcode::Wait, 18, 0, 0, 0),
    Instruction(Opcode::LoadConst, 19, 2, 0, 0),
    Instruction(Opcode::LoadConst, 20, 8, 0, 0),
    Instruction(Opcode::Set3CLed, 19, 20, 0, 0),
    Instruction(Opcode::LoadConst, 21, 3, 0, 0),
    Instruction(Opcode::LoadConst, 22, 8, 0, 0),
    Instruction(Opcode::Set3CLed, 21, 22, 0, 0),
    Instruction(Opcode::LoadConst, 23, 4, 0, 0),
    Instruction(Opcode::LoadConst, 24, 8, 0, 0),
    Instruction(Opcode::Set3CLed, 23, 24, 0, 0),
    Instruction(Opcode::Jump, 0, 2, 0, 0),
};

const uint16_t generatedProgramSize = 41;
