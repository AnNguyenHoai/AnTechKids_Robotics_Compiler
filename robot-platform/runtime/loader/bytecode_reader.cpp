#include "bytecode_reader.h"
#include <cstring>
#include <iostream>

namespace robot {
namespace execution {

bool BytecodeReader::load(const uint8_t* data, size_t size) {
    m_data = data;
    m_size = size;
    m_valid = false;
    m_error.clear();

    if (!data || size < sizeof(BytecodeHeader)) {
        m_error = "Invalid bytecode: too small";
        return false;
    }

    if (!parseHeader()) return false;
    if (!parseConstants()) return false;
    if (!parseInstructions()) return false;

    m_valid = true;
    return true;
}

const BytecodeHeader& BytecodeReader::header() const {
    return m_header;
}

const std::vector<int32_t>& BytecodeReader::constants() const {
    return m_constants;
}

const std::vector<BytecodeInstruction>& BytecodeReader::instructions() const {
    return m_instructions;
}

bool BytecodeReader::isValid() const {
    return m_valid;
}

std::string BytecodeReader::lastError() const {
    return m_error;
}

bool BytecodeReader::parseHeader() {
    if (m_size < sizeof(BytecodeHeader)) {
        m_error = "Bytecode too small for header";
        return false;
    }
    memcpy(&m_header, m_data, sizeof(BytecodeHeader));

    if (m_header.magic != MAGIC_NUMBER) {
        m_error = "Invalid magic number";
        return false;
    }
    if (m_header.versionMajor != BYTECODE_VERSION_MAJOR ||
        m_header.versionMinor != BYTECODE_VERSION_MINOR) {
        m_error = "Unsupported bytecode version";
        return false;
    }
    return true;
}

bool BytecodeReader::parseConstants() {
    // Constants are stored as sequence of int32_t after header.
    size_t offset = sizeof(BytecodeHeader);
    size_t constantsSize = m_header.constantPoolSize * sizeof(int32_t);
    if (offset + constantsSize > m_size) {
        m_error = "Invalid constant pool size";
        return false;
    }
    const int32_t* constData = reinterpret_cast<const int32_t*>(m_data + offset);
    m_constants.assign(constData, constData + m_header.constantPoolSize);
    return true;
}

bool BytecodeReader::parseInstructions() {
    size_t offset = sizeof(BytecodeHeader) + m_header.constantPoolSize * sizeof(int32_t);
    size_t instrSize = m_header.instructionCount * sizeof(BytecodeInstruction);
    if (offset + instrSize > m_size) {
        m_error = "Invalid instruction count";
        return false;
    }
    const BytecodeInstruction* instrData = reinterpret_cast<const BytecodeInstruction*>(m_data + offset);
    m_instructions.assign(instrData, instrData + m_header.instructionCount);
    return true;
}

} // namespace execution
} // namespace robot