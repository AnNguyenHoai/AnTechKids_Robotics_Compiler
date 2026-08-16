#include "execution_context.h"

namespace robot {
namespace execution {

ExecutionContext::ExecutionContext() : m_state(ExecutionState::Created) {}

ProgramCounter& ExecutionContext::programCounter() {
    return m_programCounter;
}

const ProgramCounter& ExecutionContext::programCounter() const {
    return m_programCounter;
}

OperandStack& ExecutionContext::operandStack() {
    return m_operandStack;
}

const OperandStack& ExecutionContext::operandStack() const {
    return m_operandStack;
}

CallStack& ExecutionContext::callStack() {
    return m_callStack;
}

const CallStack& ExecutionContext::callStack() const {
    return m_callStack;
}

VariableTable& ExecutionContext::variableTable() {
    return m_variableTable;
}

const VariableTable& ExecutionContext::variableTable() const {
    return m_variableTable;
}

ExecutionFlags& ExecutionContext::flags() {
    return m_flags;
}

const ExecutionFlags& ExecutionContext::flags() const {
    return m_flags;
}

void ExecutionContext::setState(ExecutionState state) {
    m_state = state;
}

ExecutionState ExecutionContext::getState() const {
    return m_state;
}

void ExecutionContext::reset() {
    m_programCounter.reset();
    m_operandStack.clear();
    m_callStack.clear();
    m_variableTable.clear();
    m_flags.reset();
    m_state = ExecutionState::Created;
}

} // namespace execution
} // namespace robot