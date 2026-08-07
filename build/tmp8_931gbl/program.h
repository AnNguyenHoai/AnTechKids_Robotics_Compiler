/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 3, 0, 0),
    Instruction(Opcode::LoadConst, 1, 0, 0, 0),
    Instruction(Opcode::CompareLT, 1, 0, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 18, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::SetLightSensorLed, 3, 4, 0, 0),
    Instruction(Opcode::LoadConst, 5, 2000, 0, 0),
    Instruction(Opcode::Wait, 5, 0, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::LoadConst, 7, 0, 0, 0),
    Instruction(Opcode::SetLightSensorLed, 6, 7, 0, 0),
    Instruction(Opcode::LoadConst, 8, 1000, 0, 0),
    Instruction(Opcode::Wait, 8, 0, 0, 0),
    Instruction(Opcode::LoadConst, 9, 1, 0, 0),
    Instruction(Opcode::Add, 1, 9, 2, 0),
    Instruction(Opcode::Store, 2, 1, 0, 0),
    Instruction(Opcode::Jump, 0, 2, 0, 0),
};

const uint16_t generatedProgramSize = 18;
