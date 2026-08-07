/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 1, 0, 0),
    Instruction(Opcode::GetTraceRaw, 0, 0, 1, 0),
    Instruction(Opcode::LoadConst, 2, 1, 0, 0),
    Instruction(Opcode::CompareEQ, 1, 2, 3, 0),
    Instruction(Opcode::JumpIfFalse, 3, 8, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 4, 5, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 9;
