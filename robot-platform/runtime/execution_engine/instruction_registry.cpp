#include "instruction_registry.h"

namespace robot {
namespace execution {

InstructionRegistry::InstructionRegistry() {
    // Stub
}

void InstructionRegistry::registerOpcode(uint32_t opcode, const OpcodeMetadata& metadata) {
    m_metadata[opcode] = metadata;
}

bool InstructionRegistry::exists(uint32_t opcode) const {
    return m_metadata.find(opcode) != m_metadata.end();
}

OpcodeMetadata InstructionRegistry::lookup(uint32_t opcode) const {
    auto it = m_metadata.find(opcode);
    if (it != m_metadata.end()) return it->second;
    return OpcodeMetadata{"unknown", "", "", 0, 0, ""};
}

std::vector<uint32_t> InstructionRegistry::getAllOpcodes() const {
    std::vector<uint32_t> keys;
    for (const auto& pair : m_metadata) keys.push_back(pair.first);
    return keys;
}

} // namespace execution
} // namespace robot