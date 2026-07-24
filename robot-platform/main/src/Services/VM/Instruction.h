#pragma once
#include <stdint.h>
#include "../../../include/generated/opcode.h"

struct Instruction
{
    Opcode opcode;
    int16_t p1;
    int16_t p2;
    int16_t p3;

    Instruction() : opcode(Opcode::LoadConst), p1(0), p2(0), p3(0) {}
    Instruction(Opcode op, int16_t param1, int16_t param2, int16_t param3)
        : opcode(op), p1(param1), p2(param2), p3(param3) {}
};