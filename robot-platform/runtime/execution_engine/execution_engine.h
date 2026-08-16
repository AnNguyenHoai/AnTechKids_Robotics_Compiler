#pragma once

#include "execution_context.h"
#include "execution_state.h"
#include "execution_result.h"
#include "scheduler.h"
#include "runtime_services.h"
#include "../robot_dispatcher/robot_api_dispatcher.h"
#include "../robot_dispatcher/i_robot_api.h"
#include "dispatcher/instruction_dispatcher.h"
#include "registry/instruction_registry.h"
#include "../loader/program.h"
#include "../vm/virtual_machine.h"
#include <memory>
#include <string>

namespace robot {
namespace execution {

class ExecutionEngine {
public:
    ExecutionEngine();

    // Program loading
    ExecutionResult loadProgram(const Program& program);
    ExecutionResult loadBytecode(const uint8_t* bytecode, size_t size);

    // Execution control (delegates to VM)
    ExecutionResult initialize();
    ExecutionResult execute();
    ExecutionResult executeStep();
    ExecutionResult pause();
    ExecutionResult resume();
    ExecutionResult stop();

    // State queries
    ExecutionState getState() const;
    ExecutionResult getLastResult() const;

    // Accessors
    ExecutionContext& context();
    InstructionDispatcher& dispatcher();
    RobotApiDispatcher& apiDispatcher();
    RuntimeServices& services();
    Scheduler& scheduler();

private:
    ExecutionContext m_context;
    InstructionDispatcher m_dispatcher;
    InstructionRegistry m_registry;
    std::shared_ptr<IRobotApi> m_robotApi;
    RobotApiDispatcher m_apiDispatcher;
    RuntimeServices m_services;
    Scheduler m_scheduler;
    std::unique_ptr<VirtualMachine> m_vm;
    ExecutionState m_state;
    ExecutionResult m_lastResult;
};

} // namespace execution
} // namespace robot