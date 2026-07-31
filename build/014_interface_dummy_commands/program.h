/******************************************************************************
 * AUTO GENERATED FILE
 *
 * DO NOT EDIT MANUALLY.
 ******************************************************************************/

#pragma once

const Instruction generatedProgram[] =
{
    Instruction(Opcode::LoadConst, 0, 1, 0, 0),
    Instruction(Opcode::LoadConst, 1, 90, 0, 0),
    Instruction(Opcode::SetServo, 0, 1, 0, 0),
    Instruction(Opcode::LoadConst, 2, 2, 0, 0),
    Instruction(Opcode::LoadConst, 3, 1, 0, 0),
    Instruction(Opcode::Set3CLed, 2, 3, 0, 0),
    Instruction(Opcode::LoadConst, 4, 3, 0, 0),
    Instruction(Opcode::LoadConst, 5, 0, 0, 0),
    Instruction(Opcode::SetLightSensorLed, 4, 5, 0, 0),
    Instruction(Opcode::LoadConst, 6, 1, 0, 0),
    Instruction(Opcode::LoadConst, 7, 2, 0, 0),
    Instruction(Opcode::LoadConst, 8, 70, 0, 0),
    Instruction(Opcode::LoadConst, 9, 360, 0, 0),
    Instruction(Opcode::SetMotorStraightAngle, 6, 7, 8, 9),
    Instruction(Opcode::LoadConst, 10, 70, 0, 0),
    Instruction(Opcode::LoadConst, 11, 17, 0, 0),
    Instruction(Opcode::LineIntersectionStop, 10, 11, 0, 0),
};

const uint16_t generatedProgramSize = 17;
