/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 1, 1, 0, 0),
    Instruction(Opcode::GetTraceRaw, 1, 0, 2, 0),
    Instruction(Opcode::Store, 2, 0, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::CompareEQ, 0, 3, 4, 0),
    Instruction(Opcode::JumpIfFalse, 4, 10, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 5, 6, 0, 0),
    Instruction(Opcode::Jump, 0, 13, 0, 0),
    Instruction(Opcode::LoadConst, 7, 1, 0, 0),
    Instruction(Opcode::LoadConst, 8, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 7, 8, 0, 0),
    Instruction(Opcode::LoadConst, 9, 50, 0, 0),
    Instruction(Opcode::Wait, 9, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 16;
