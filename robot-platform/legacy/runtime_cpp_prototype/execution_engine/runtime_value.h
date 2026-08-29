#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>

namespace robot {
namespace execution {

enum class ValueType : uint8_t {
    Integer,
    Float,
    Boolean,
    // Future: String, Array, etc.
};

class RuntimeValue {
public:
    RuntimeValue();
    explicit RuntimeValue(int32_t value);
    explicit RuntimeValue(float value);
    explicit RuntimeValue(bool value);

    ValueType type() const;

    int32_t asInteger() const;
    float asFloat() const;
    bool asBoolean() const;

    bool isInteger() const;
    bool isFloat() const;
    bool isBoolean() const;

    bool operator==(const RuntimeValue& other) const;
    bool operator!=(const RuntimeValue& other) const;

    void reset();

private:
    ValueType m_type;
    union {
        int32_t intVal;
        float floatVal;
        bool boolVal;
    } m_data;
};

} // namespace execution
} // namespace robot