#pragma once

#include "runtime_value.h"
#include <unordered_map>
#include <cstdint>
#include <stdexcept>

namespace robot {
namespace execution {

using VariableId = uint32_t;

class VariableTable {
public:
    VariableTable();

    void declare(VariableId id, const RuntimeValue& initialValue = RuntimeValue(0));
    bool exists(VariableId id) const;
    RuntimeValue read(VariableId id) const;
    void write(VariableId id, const RuntimeValue& value);
    void remove(VariableId id);
    void clear();
    size_t size() const;

private:
    std::unordered_map<VariableId, RuntimeValue> m_variables;
};

} // namespace execution
} // namespace robot