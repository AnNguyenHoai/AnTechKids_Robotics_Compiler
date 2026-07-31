#pragma once
#include <stdint.h>
#include "../../../include/generated/opcode.h"

struct Instruction
{
    Opcode opcode;
    int32_t p1;
    int32_t p2;
    int32_t p3;
    int32_t p4;

    Instruction() : opcode(Opcode::LoadConst), p1(0), p2(0), p3(0), p4(0) {}
    Instruction(Opcode op, int32_t param1, int32_t param2, int32_t param3, int32_t param4 = 0)
        : opcode(op), p1(param1), p2(param2), p3(param3), p4(param4) {}
};