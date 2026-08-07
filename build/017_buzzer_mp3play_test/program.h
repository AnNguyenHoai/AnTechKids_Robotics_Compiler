/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 1, 0, 0),
    Instruction(Opcode::LoadConst, 1, 3, 0, 0),
    Instruction(Opcode::Set3CLed, 0, 1, 0, 0),
    Instruction(Opcode::LoadConst, 2, 2, 0, 0),
    Instruction(Opcode::LoadConst, 3, 3, 0, 0),
    Instruction(Opcode::Set3CLed, 2, 3, 0, 0),
    Instruction(Opcode::LoadConst, 4, 5000, 0, 0),
    Instruction(Opcode::Wait, 4, 0, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::SetMp3Play, 5, 0, 0, 0),
    Instruction(Opcode::LoadConst, 6, 5, 0, 0),
    Instruction(Opcode::LoadConst, 7, 0, 0, 0),
    Instruction(Opcode::CompareLT, 7, 6, 8, 0),
    Instruction(Opcode::JumpIfFalse, 8, 22, 0, 0),
    Instruction(Opcode::LoadConst, 9, 1, 0, 0),
    Instruction(Opcode::SetMp3Play, 9, 0, 0, 0),
    Instruction(Opcode::LoadConst, 10, 0.5, 0, 0),
    Instruction(Opcode::Wait, 10, 0, 0, 0),
    Instruction(Opcode::LoadConst, 11, 1, 0, 0),
    Instruction(Opcode::Add, 7, 11, 8, 0),
    Instruction(Opcode::Store, 8, 7, 0, 0),
    Instruction(Opcode::Jump, 0, 12, 0, 0),
};

const uint16_t generatedProgramSize = 22;
