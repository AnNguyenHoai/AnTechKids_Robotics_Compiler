#pragma once
#include <string>
#include <unordered_map>
#include "Opcode.h"

/**
 * Singleton registry for opcode metadata.
 * Maps Opcode → name, operand count, description.
 */
class OpcodeRegistry {
public:
    static OpcodeRegistry& instance();

    std::string getName(Opcode op) const;
    uint8_t getOperandCount(Opcode op) const;
    std::string getDescription(Opcode op) const;

private:
    OpcodeRegistry();
    std::unordered_map<Opcode, std::string> names;
    std::unordered_map<Opcode, uint8_t> operandCounts;
    std::unordered_map<Opcode, std::string> descriptions;
};