#pragma once

#include "vm_state.h"
#include "vm_statistics.h"
#include "fetch_stage.h"
#include "execute_stage.h"
#include "../loader/program.h"
#include "execution_context.h"
#include "execution_result.h"
#include "runtime_services.h"
#include "robot_api_dispatcher.h"
#include "dispatcher/instruction_dispatcher.h"
#include "registry/instruction_registry.h"
#include "instruction/instruction_context.h"
#include <memory>
#include <functional>

namespace robot {
namespace execution {

class VirtualMachine {
public:
    VirtualMachine(InstructionDispatcher& dispatcher,
                   RuntimeServices& services,
                   RobotApiDispatcher& apiDispatcher);

    // Program management
    ExecutionResult loadProgram(const Program& program);
    ExecutionResult initialize();

    // Execution control
    ExecutionResult start();
    ExecutionResult step();
    ExecutionResult run();
    ExecutionResult pause();
    ExecutionResult resume();
    ExecutionResult stop();
    ExecutionResult reset();

    // State queries
    VMState state() const;
    const ExecutionContext& context() const;
    ExecutionContext& context();
    const VMStatistics& statistics() const;

    // Callbacks for diagnostics
    using StepCallback = std::function<void(const ProgramInstruction&, const ExecutionResult&)>;
    void setStepCallback(StepCallback callback);

private:
    ExecutionResult executeInstruction(const ProgramInstruction& ins);

    ExecutionContext m_context;
    InstructionRegistry m_registry; // owned by engine, but we hold reference
    InstructionDispatcher& m_dispatcher;
    RuntimeServices& m_services;
    RobotApiDispatcher& m_apiDispatcher;
    std::unique_ptr<InstructionContext> m_instructionContext;
    std::unique_ptr<FetchStage> m_fetchStage;
    std::unique_ptr<ExecuteStage> m_executeStage;
    std::unique_ptr<Program> m_program;

    VMState m_state;
    VMStatistics m_statistics;
    StepCallback m_stepCallback;
};

} // namespace execution
} // namespace robot