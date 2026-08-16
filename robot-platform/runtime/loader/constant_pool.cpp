#include "constant_pool.h"

namespace robot {
namespace execution {

size_t ConstantPool::addInteger(int32_t value) {
    m_constants.emplace_back(value);
    return m_constants.size() - 1;
}

size_t ConstantPool::addBoolean(bool value) {
    m_constants.emplace_back(value);
    return m_constants.size() - 1;
}

size_t ConstantPool::addFloat(float value) {
    m_constants.emplace_back(value);
    return m_constants.size() - 1;
}

size_t ConstantPool::addString(const std::string& value) {
    // For now, we don't support string constants; we'll store as integer placeholder.
    // In future, we'll extend RuntimeValue to support string.
    m_constants.emplace_back(static_cast<int32_t>(0)); // placeholder
    return m_constants.size() - 1;
}

std::optional<RuntimeValue> ConstantPool::get(size_t index) const {
    if (index < m_constants.size()) {
        return m_constants[index];
    }
    return std::nullopt;
}

size_t ConstantPool::size() const {
    return m_constants.size();
}

void ConstantPool::clear() {
    m_constants.clear();
}

} // namespace execution
} // namespace robot