#include "operand_stack.h"

namespace robot {
namespace execution {

OperandStack::OperandStack(size_t capacity) : m_capacity(capacity) {
    m_stack.reserve(capacity);
}

void OperandStack::push(const RuntimeValue& value) {
    if (m_stack.size() >= m_capacity) {
        throw std::overflow_error("OperandStack overflow");
    }
    m_stack.push_back(value);
}

RuntimeValue OperandStack::pop() {
    if (m_stack.empty()) {
        throw std::underflow_error("OperandStack underflow");
    }
    RuntimeValue val = m_stack.back();
    m_stack.pop_back();
    return val;
}

RuntimeValue OperandStack::peek() const {
    if (m_stack.empty()) {
        throw std::underflow_error("OperandStack empty");
    }
    return m_stack.back();
}

void OperandStack::clear() {
    m_stack.clear();
}

size_t OperandStack::size() const {
    return m_stack.size();
}

bool OperandStack::empty() const {
    return m_stack.empty();
}

size_t OperandStack::capacity() const {
    return m_capacity;
}

} // namespace execution
} // namespace robot