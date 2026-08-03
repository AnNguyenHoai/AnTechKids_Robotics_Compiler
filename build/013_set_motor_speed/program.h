/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 80, 0, 0),
    Instruction(Opcode::LoadConst, 1, 80, 0, 0),
    Instruction(Opcode::SetMotorSpeed, 0, 1, 0, 0),
    Instruction(Opcode::LoadConst, 2, 2000, 0, 0),
    Instruction(Opcode::Wait, 2, 0, 0, 0),
    Instruction(Opcode::LoadConst, 3, 0, 0, 0),
    Instruction(Opcode::LoadConst, 4, 0, 0, 0),
    Instruction(Opcode::SetMotorSpeed, 3, 4, 0, 0),
    Instruction(Opcode::LoadConst, 5, 80, 0, 0),
    Instruction(Opcode::Neg, 5, 0, 6, 0),
    Instruction(Opcode::LoadConst, 7, 80, 0, 0),
    Instruction(Opcode::Neg, 7, 0, 8, 0),
    Instruction(Opcode::SetMotorSpeed, 6, 8, 0, 0),
    Instruction(Opcode::LoadConst, 9, 2000, 0, 0),
    Instruction(Opcode::Wait, 9, 0, 0, 0),
    Instruction(Opcode::LoadConst, 10, 0, 0, 0),
    Instruction(Opcode::LoadConst, 11, 0, 0, 0),
    Instruction(Opcode::SetMotorSpeed, 10, 11, 0, 0),
};

const uint16_t generatedProgramSize = 18;
