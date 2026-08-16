#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace robot {
namespace execution {

struct OpcodeMetadata {
    std::string name;
    std::string semantic;    // e.g., Native, Rewrite, NOP, Stub
    std::string category;
    uint32_t priority;       // P0, P1, etc.
    uint32_t operandCount;
    std::string description;
};

class InstructionRegistry {
public:
    InstructionRegistry();

    void registerOpcode(uint32_t opcode, const OpcodeMetadata& metadata);
    bool exists(uint32_t opcode) const;
    OpcodeMetadata lookup(uint32_t opcode) const;
    std::vector<uint32_t> getAllOpcodes() const;

private:
    std::unordered_map<uint32_t, OpcodeMetadata> m_metadata;
};

} // namespace execution
} // namespace robot