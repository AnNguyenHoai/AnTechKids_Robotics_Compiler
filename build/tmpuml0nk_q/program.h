/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::ReadUltrasonic, 0, 0, 0, 0),
    Instruction(Opcode::LoadConst, 1, 10, 0, 0),
    Instruction(Opcode::CompareGT, 0, 1, 2, 0),
    Instruction(Opcode::JumpIfFalse, 2, 7, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::SetMp3Play, 3, 0, 0, 0),
    Instruction(Opcode::Jump, 0, 10, 0, 0),
    Instruction(Opcode::LoadConst, 4, 1, 0, 0),
    Instruction(Opcode::LoadConst, 5, 1, 0, 0),
    Instruction(Opcode::SetLightSensorLed, 4, 5, 0, 0),
    Instruction(Opcode::Jump, 0, 0, 0, 0),
};

const uint16_t generatedProgramSize = 11;
