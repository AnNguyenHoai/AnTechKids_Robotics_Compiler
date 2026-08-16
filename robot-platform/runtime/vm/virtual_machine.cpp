#include "virtual_machine.h"
#include "execution_state.h"

namespace robot {
namespace execution {

VirtualMachine::VirtualMachine(InstructionDispatcher& dispatcher,
                               RuntimeServices& services,
                               RobotApiDispatcher& apiDispatcher)
    : m_dispatcher(dispatcher), m_services(services), m_apiDispatcher(apiDispatcher),
      m_state(VMState::Created), m_program(nullptr) {
    m_instructionContext = std::make_unique<InstructionContext>(m_context, m_services, m_apiDispatcher);
    m_fetchStage = std::make_unique<FetchStage>();
    m_executeStage = std::make_unique<ExecuteStage>(m_dispatcher, *m_instructionContext);
}

ExecutionResult VirtualMachine::loadProgram(const Program& program) {
    if (program.empty()) {
        return ExecutionResult(ExecutionStatus::Failure, 1, "Cannot load empty program");
    }
    m_program = std::make_unique<Program>(program);
    m_state = VMState::Loaded;
    m_statistics.reset();
    return ExecutionResult(ExecutionStatus::Success);
}

ExecutionResult VirtualMachine::initialize() {
    if (!m_program) {
        return ExecutionResult(ExecutionStatus::Failure, 2, "No program loaded");
    }
    m_context.reset();
    m_context.programCounter().set(m_program->entryPoint());
    m_context.setState(ExecutionState::Initialized);
    m_state = VMState::Ready;
    return ExecutionResult(ExecutionStatus::Success);
}

ExecutionResult VirtualMachine::start() {
    if (m_state == VMState::Ready || m_state == VMState::Loaded) {
        m_state = VMState::Running;
        m_context.flags().setRunning(true);
        m_statistics.startExecution();
        return ExecutionResult(ExecutionStatus::Success);
    }
    return ExecutionResult(ExecutionStatus::Failure, 3, "Cannot start from current state");
}

ExecutionResult VirtualMachine::step() {
    if (m_state == VMState::Running || m_state == VMState::Paused) {
        if (!m_program) {
            return ExecutionResult(ExecutionStatus::Failure, 4, "No program loaded");
        }

        // Fetch instruction
        auto maybeIns = m_fetchStage->fetch(*m_program, m_context);
        if (!maybeIns) {
            return ExecutionResult(ExecutionStatus::Failure, 5, "Fetch failed: " + m_fetchStage->lastError());
        }
        const auto& ins = *maybeIns;

        // Execute
        auto result = m_executeStage->execute(ins);
        if (!result.isSuccess()) {
            m_state = VMState::Error;
            m_statistics.incrementErrors();
            if (m_stepCallback) {
                m_stepCallback(ins, result);
            }
            return result;
        }

        m_statistics.incrementInstructions();

        // Update PC if not advanced by handler (and not completed)
        if (!m_context.flags().isCompleted() && !m_context.flags().isError()) {
            // If instruction did not change PC, advance
            uint32_t pc = m_context.programCounter().current();
            // Check if instruction modified PC (jump/return/end). For simplicity, we advance by default.
            // Actually, handlers should handle PC properly. For core instructions, they do.
            // We'll trust the handler.
        }

        if (m_context.flags().isCompleted()) {
            m_state = VMState::Completed;
            m_statistics.stopExecution();
        }

        if (m_stepCallback) {
            m_stepCallback(ins, result);
        }

        return result;
    }
    return ExecutionResult(ExecutionStatus::Failure, 6, "VM not in running/paused state");
}

ExecutionResult VirtualMachine::run() {
    auto startResult = start();
    if (!startResult.isSuccess()) {
        return startResult;
    }

    while (m_state == VMState::Running) {
        auto stepResult = step();
        if (!stepResult.isSuccess()) {
            return stepResult;
        }
        if (m_state == VMState::Completed) {
            break;
        }
        // Check for pause request or stop
        if (m_state == VMState::Paused || m_state == VMState::Stopped) {
            break;
        }
    }
    return ExecutionResult(ExecutionStatus::Success);
}

ExecutionResult VirtualMachine::pause() {
    if (m_state == VMState::Running) {
        m_state = VMState::Paused;
        m_context.flags().setPaused(true);
        m_statistics.stopExecution();
        return ExecutionResult(ExecutionStatus::Success);
    }
    return ExecutionResult(ExecutionStatus::Failure, 7, "Cannot pause: not running");
}

ExecutionResult VirtualMachine::resume() {
    if (m_state == VMState::Paused) {
        m_state = VMState::Running;
        m_context.flags().setPaused(false);
        m_statistics.startExecution();
        return ExecutionResult(ExecutionStatus::Success);
    }
    return ExecutionResult(ExecutionStatus::Failure, 8, "Cannot resume: not paused");
}

ExecutionResult VirtualMachine::stop() {
    m_state = VMState::Stopped;
    m_context.flags().setRunning(false);
    m_statistics.stopExecution();
    return ExecutionResult(ExecutionStatus::Success);
}

ExecutionResult VirtualMachine::reset() {
    m_context.reset();
    m_state = VMState::Created;
    m_statistics.reset();
    m_program.reset();
    return ExecutionResult(ExecutionStatus::Success);
}

VMState VirtualMachine::state() const {
    return m_state;
}

const ExecutionContext& VirtualMachine::context() const {
    return m_context;
}

ExecutionContext& VirtualMachine::context() {
    return m_context;
}

const VMStatistics& VirtualMachine::statistics() const {
    return m_statistics;
}

void VirtualMachine::setStepCallback(StepCallback callback) {
    m_stepCallback = callback;
}

} // namespace execution
} // namespace robot