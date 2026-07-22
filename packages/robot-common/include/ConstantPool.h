#pragma once
#include <vector>
#include <variant>
#include <string>
#include <cstdint>

/**
 * Deduplicated constant pool.
 * Supports integers, floats, strings, booleans.
 * Returns an index for each unique constant.
 */
class ConstantPool {
public:
    using Constant = std::variant<int64_t, double, std::string, bool>;

    uint32_t add(int64_t v);
    uint32_t add(double v);
    uint32_t add(const std::string& v);
    uint32_t add(bool v);

    const Constant& get(uint32_t index) const;
    size_t size() const { return constants.size(); }

private:
    std::vector<Constant> constants;

    template<typename T>
    uint32_t findOrAdd(const T& value);
};