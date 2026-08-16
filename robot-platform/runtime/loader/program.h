#pragma once

#include "constant_pool.h"
#include "execution_types.h"
#include <vector>
#include <cstdint>
#include <string>

namespace robot {
namespace execution {

struct ProgramInstruction {
    uint32_t opcode;
    std::vector<uint32_t> operands;
};

/**
 * Program – immutable representation of a loaded runtime program.
 */
class Program {
public:
    Program() = default;

    // Setters (used during loading)
    void setEntryPoint(uint32_t entry);
    void setInstructions(const std::vector<ProgramInstruction>& instrs);
    void setConstantPool(const ConstantPool& pool);
    void setMetadata(const std::string& key, const std::string& value);

    // Getters
    uint32_t entryPoint() const;
    size_t instructionCount() const;
    const ProgramInstruction& getInstruction(size_t index) const;
    const ConstantPool& constantPool() const;
    std::string metadata(const std::string& key) const;

    // Utility
    size_t size() const;
    bool empty() const;

private:
    uint32_t m_entryPoint = 0;
    std::vector<ProgramInstruction> m_instructions;
    ConstantPool m_constantPool;
    std::unordered_map<std::string, std::string> m_metadata;
};

} // namespace execution
} // namespace robot