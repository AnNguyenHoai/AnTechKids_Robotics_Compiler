#include "runtime_value.h"

namespace robot {
namespace execution {

RuntimeValue::RuntimeValue() : m_type(ValueType::Integer) {
    m_data.intVal = 0;
}

RuntimeValue::RuntimeValue(int32_t value) : m_type(ValueType::Integer) {
    m_data.intVal = value;
}

RuntimeValue::RuntimeValue(float value) : m_type(ValueType::Float) {
    m_data.floatVal = value;
}

RuntimeValue::RuntimeValue(bool value) : m_type(ValueType::Boolean) {
    m_data.boolVal = value;
}

ValueType RuntimeValue::type() const {
    return m_type;
}

int32_t RuntimeValue::asInteger() const {
    if (m_type != ValueType::Integer)
        throw std::runtime_error("RuntimeValue is not integer");
    return m_data.intVal;
}

float RuntimeValue::asFloat() const {
    if (m_type != ValueType::Float)
        throw std::runtime_error("RuntimeValue is not float");
    return m_data.floatVal;
}

bool RuntimeValue::asBoolean() const {
    if (m_type != ValueType::Boolean)
        throw std::runtime_error("RuntimeValue is not boolean");
    return m_data.boolVal;
}

bool RuntimeValue::isInteger() const {
    return m_type == ValueType::Integer;
}

bool RuntimeValue::isFloat() const {
    return m_type == ValueType::Float;
}

bool RuntimeValue::isBoolean() const {
    return m_type == ValueType::Boolean;
}

bool RuntimeValue::operator==(const RuntimeValue& other) const {
    if (m_type != other.m_type) return false;
    switch (m_type) {
        case ValueType::Integer: return m_data.intVal == other.m_data.intVal;
        case ValueType::Float:   return m_data.floatVal == other.m_data.floatVal;
        case ValueType::Boolean: return m_data.boolVal == other.m_data.boolVal;
        default: return false;
    }
}

bool RuntimeValue::operator!=(const RuntimeValue& other) const {
    return !(*this == other);
}

void RuntimeValue::reset() {
    m_type = ValueType::Integer;
    m_data.intVal = 0;
}

} // namespace execution
} // namespace robot