#pragma once
#include <vector>
#include <cstdint>
#include "Opcode.h"
#include "Operand.h"

/**
 * An instruction is the smallest executable unit.
 * It has a fixed opcode and a dynamic list of operands.
 */
struct Instruction {
    Opcode opcode;
    std::vector<Operand> operands;

    Instruction() = default;
    explicit Instruction(Opcode op) : opcode(op) {}
    Instruction(Opcode op, const std::vector<Operand>& ops)
        : opcode(op), operands(ops) {}
};