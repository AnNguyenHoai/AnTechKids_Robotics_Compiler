#include "variable_table.h"

namespace robot {
namespace execution {

VariableTable::VariableTable() {}

void VariableTable::declare(VariableId id, const RuntimeValue& initialValue) {
    if (m_variables.find(id) != m_variables.end()) {
        throw std::runtime_error("Variable already declared");
    }
    m_variables[id] = initialValue;
}

bool VariableTable::exists(VariableId id) const {
    return m_variables.find(id) != m_variables.end();
}

RuntimeValue VariableTable::read(VariableId id) const {
    auto it = m_variables.find(id);
    if (it == m_variables.end()) {
        throw std::runtime_error("Variable not found");
    }
    return it->second;
}

void VariableTable::write(VariableId id, const RuntimeValue& value) {
    auto it = m_variables.find(id);
    if (it == m_variables.end()) {
        throw std::runtime_error("Variable not found");
    }
    it->second = value;
}

void VariableTable::remove(VariableId id) {
    auto it = m_variables.find(id);
    if (it != m_variables.end()) {
        m_variables.erase(it);
    }
}

void VariableTable::clear() {
    m_variables.clear();
}

size_t VariableTable::size() const {
    return m_variables.size();
}

} // namespace execution
} // namespace robot