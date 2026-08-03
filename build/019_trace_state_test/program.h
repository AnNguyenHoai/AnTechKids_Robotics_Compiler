/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 1, 0, 0),
    Instruction(Opcode::LoadConst, 1, 1, 0, 0),
    Instruction(Opcode::GetTraceState, 0, 1, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 8, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::LoadConst, 4, 0, 0, 0),
    Instruction(Opcode::Set3CLed, 3, 4, 0, 0),
    Instruction(Opcode::Jump, 0, 11, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 5, 6, 0, 0),
    Instruction(Opcode::LoadConst, 7, 100, 0, 0),
    Instruction(Opcode::Wait, 7, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 14;
