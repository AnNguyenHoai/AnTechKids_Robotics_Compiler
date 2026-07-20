
/******************************************************************************
 * AUTO GENERATED FILE
 * DO NOT EDIT MANUALLY
 ******************************************************************************/

#pragma once

#include <stdint.h>

enum class Opcode : uint8_t
{
    Forward = 2,
    Backward = 3,
    TurnLeft = 4,
    TurnRight = 5,
    Wait = 7,
    Stop = 6,
    LoadConst = 1,
    CompareEQ = 8,
    CompareNE = 9,
    CompareLT = 10,
    CompareLE = 11,
    CompareGT = 12,
    CompareGE = 13,
    Jump = 14,
    JumpIfFalse = 15,
    JumpIfTrue = 16,
    Label = 17,
    Add = 20,
    Sub = 21,
    Mul = 22,
    Div = 23,
    Mod = 24,
    Pow = 25,
    Neg = 26,
};
