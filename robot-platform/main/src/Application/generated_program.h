/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 10, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::CompareLT, 1, 0, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 10, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::SetMp3Play, 3, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::Add, 1, 4, 2, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 2, 0, 0),
};

const uint16_t generatedProgramSize = 10;
