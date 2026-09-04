#pragma once

#include "program_counter.h"
#include "operand_stack.h"
#include "call_stack.h"
#include "variable_table.h"
#include "execution_flags.h"
#include "execution_state.h"
#include <cstdint>

namespace robot {
namespace execution {

class ExecutionContext {
public:
    ExecutionContext();

    // Component accessors
    ProgramCounter& programCounter();
    const ProgramCounter& programCounter() const;

    OperandStack& operandStack();
    const OperandStack& operandStack() const;

    CallStack& callStack();
    const CallStack& callStack() const;

    VariableTable& variableTable();
    const VariableTable& variableTable() const;

    ExecutionFlags& flags();
    const ExecutionFlags& flags() const;

    // State management
    void setState(ExecutionState state);
    ExecutionState getState() const;
    void reset();

private:
    ProgramCounter m_programCounter;
    OperandStack m_operandStack;
    CallStack m_callStack;
    VariableTable m_variableTable;
    ExecutionFlags m_flags;
    ExecutionState m_state;
};

} // namespace execution
} // namespace robot