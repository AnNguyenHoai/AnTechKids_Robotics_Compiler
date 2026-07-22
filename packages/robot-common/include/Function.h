#pragma once
#include <string>
#include <vector>
#include "Instruction.h"

/**
 * A function is a named sequence of instructions.
 * It represents an executable procedure.
 */
class Function {
public:
    std::string name;
    std::vector<Instruction> instructions;

    Function() = default;
    explicit Function(const std::string& n) : name(n) {}
};