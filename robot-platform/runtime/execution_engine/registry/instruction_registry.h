#pragma once

#include "execution_types.h"
#include <cstdint>
#include <unordered_map>
#include <string>
#include <optional>

namespace robot {
namespace execution {

struct InstructionMetadata {
    uint32_t opcode;
    std::string name;
    InstructionCategory category;
    Semantic semantic;
    uint8_t operandCount;
    bool supported;
    bool deprecated;
    std::string description;
};

class InstructionRegistry {
public:
    InstructionRegistry();

    void registerInstruction(const InstructionMetadata& metadata);
    bool exists(uint32_t opcode) const;
    std::optional<InstructionMetadata> lookup(uint32_t opcode) const;
    void clear();

private:
    std::unordered_map<uint32_t, InstructionMetadata> m_metadata;
};

} // namespace execution
} // namespace robot