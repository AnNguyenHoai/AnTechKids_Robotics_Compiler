#pragma once
#include <variant>
#include <string>
#include <cstdint>

/**
 * Type of an operand.
 */
enum class OperandType {
    Integer,
    Float,
    Boolean,
    String,
    Variable,
    Label,
    Enum
};

/**
 * Type‑safe operand that can hold any supported value.
 */
class Operand {
public:
    using Value = std::variant<int64_t, double, bool, std::string, uint32_t, uint32_t, int>;

    Operand() = default;

    explicit Operand(int64_t v)           : type(OperandType::Integer), value(v) {}
    explicit Operand(double v)            : type(OperandType::Float),   value(v) {}
    explicit Operand(bool v)              : type(OperandType::Boolean), value(v) {}
    explicit Operand(const std::string& v): type(OperandType::String),  value(v) {}

    // For Variable, Label, Enum – we reuse uint32_t as an index/id
    explicit Operand(uint32_t v, OperandType t)
        : type(t), value(v) {}

    OperandType getType() const { return type; }
    const Value& getValue() const { return value; }

    // Accessors (use with care)
    int64_t asInteger() const { return std::get<int64_t>(value); }
    double  asFloat()   const { return std::get<double>(value); }
    bool    asBoolean() const { return std::get<bool>(value); }
    const std::string& asString() const { return std::get<std::string>(value); }
    uint32_t asIndex()  const { return std::get<uint32_t>(value); }

private:
    OperandType type;
    Value value;
};