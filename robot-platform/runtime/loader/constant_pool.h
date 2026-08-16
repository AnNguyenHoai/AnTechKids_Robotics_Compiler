#pragma once

#include "runtime_value.h"
#include <vector>
#include <cstdint>
#include <optional>

namespace robot {
namespace execution {

/**
 * ConstantPool – stores constants used by the program.
 *
 * Constants are indexed and accessed via index.
 * Supports integers, booleans, and future types.
 */
class ConstantPool {
public:
    ConstantPool() = default;

    // Add a constant; returns its index.
    size_t addInteger(int32_t value);
    size_t addBoolean(bool value);
    size_t addFloat(float value);
    size_t addString(const std::string& value);

    // Retrieve constant by index.
    std::optional<RuntimeValue> get(size_t index) const;

    size_t size() const;

    void clear();

private:
    std::vector<RuntimeValue> m_constants;
};

} // namespace execution
} // namespace robot