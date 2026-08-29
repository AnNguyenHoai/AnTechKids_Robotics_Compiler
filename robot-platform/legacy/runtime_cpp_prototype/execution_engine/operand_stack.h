#pragma once

#include "runtime_value.h"
#include <vector>
#include <cstddef>
#include <stdexcept>

namespace robot {
namespace execution {

class OperandStack {
public:
    explicit OperandStack(size_t capacity = 1024);

    void push(const RuntimeValue& value);
    RuntimeValue pop();
    RuntimeValue peek() const;
    void clear();
    size_t size() const;
    bool empty() const;
    size_t capacity() const;

private:
    std::vector<RuntimeValue> m_stack;
    size_t m_capacity;
};

} // namespace execution
} // namespace robot