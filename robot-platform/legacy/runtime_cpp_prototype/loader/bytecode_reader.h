#pragma once

#include "bytecode_format.h"
#include <vector>
#include <cstdint>
#include <string>

namespace robot {
namespace execution {

class BytecodeReader {
public:
    // Load bytecode from raw buffer.
    bool load(const uint8_t* data, size_t size);

    // Header access
    const BytecodeHeader& header() const;

    // Access to constants area
    const std::vector<int32_t>& constants() const;

    // Access to instructions area
    const std::vector<BytecodeInstruction>& instructions() const;

    // Validation
    bool isValid() const;
    std::string lastError() const;

private:
    bool parseHeader();
    bool parseConstants();
    bool parseInstructions();

    const uint8_t* m_data = nullptr;
    size_t m_size = 0;
    bool m_valid = false;
    std::string m_error;

    BytecodeHeader m_header;
    std::vector<int32_t> m_constants;
    std::vector<BytecodeInstruction> m_instructions;
};

} // namespace execution
} // namespace robot