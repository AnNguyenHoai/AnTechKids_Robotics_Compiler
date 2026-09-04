#include "program.h"
#include <stdexcept>

namespace robot {
namespace execution {

void Program::setEntryPoint(uint32_t entry) {
    m_entryPoint = entry;
}

void Program::setInstructions(const std::vector<ProgramInstruction>& instrs) {
    m_instructions = instrs;
}

void Program::setConstantPool(const ConstantPool& pool) {
    m_constantPool = pool;
}

void Program::setMetadata(const std::string& key, const std::string& value) {
    m_metadata[key] = value;
}

uint32_t Program::entryPoint() const {
    return m_entryPoint;
}

size_t Program::instructionCount() const {
    return m_instructions.size();
}

const ProgramInstruction& Program::getInstruction(size_t index) const {
    if (index >= m_instructions.size()) {
        throw std::out_of_range("Instruction index out of range");
    }
    return m_instructions[index];
}

const ConstantPool& Program::constantPool() const {
    return m_constantPool;
}

std::string Program::metadata(const std::string& key) const {
    auto it = m_metadata.find(key);
    if (it != m_metadata.end()) {
        return it->second;
    }
    return "";
}

size_t Program::size() const {
    return m_instructions.size();
}

bool Program::empty() const {
    return m_instructions.empty();
}

} // namespace execution
} // namespace robot