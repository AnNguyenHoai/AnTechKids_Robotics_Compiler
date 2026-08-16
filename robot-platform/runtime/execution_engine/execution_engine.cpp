#include "execution_engine.h"
#include "instruction/instruction_factory.h"
#include "../robot_dispatcher/robot_api_dispatcher.h"
#include "../robot_dispatcher/dummy_robot_api.h"
#include "../loader/program_loader.h"
#include <iostream>

// Include ESP32RobotApi only when building for ESP32
#ifdef ESP32
#include "../platform/esp32/esp32_robot_api.h"
#endif

// DummyRobotApi implementation (fallback for non-ESP32)
#ifndef ESP32
// The local DummyRobotApi definition is replaced by including the header
// but we keep the fallback if needed.
#endif

namespace robot {
namespace execution {

ExecutionEngine::ExecutionEngine()
    : m_state(ExecutionState::Created),
      m_lastResult(true),
      m_dispatcher(InstructionFactory::defaultFactory()),
      m_apiDispatcher(m_robotApi) {
    m_dispatcher.setRegistry(m_registry);

#ifdef ESP32
    m_robotApi = std::make_shared<ESP32RobotApi>();
#else
    m_robotApi = std::make_shared<DummyRobotApi>();
#endif

    // Re-initialize dispatcher with the new API
    m_apiDispatcher = RobotApiDispatcher(m_robotApi);
    m_vm = std::make_unique<VirtualMachine>(m_dispatcher, m_services, m_apiDispatcher);
}


ExecutionResult ExecutionEngine::loadProgram(const Program& program) {
    auto result = m_vm->loadProgram(program);
    if (result.isSuccess()) {
        m_state = ExecutionState::Loaded;
    }
    return result;
}

ExecutionResult ExecutionEngine::loadBytecode(const uint8_t* bytecode, size_t size) {
    Program program;
    ProgramLoader loader;
    auto result = loader.load(bytecode, size, program);
    if (!result.isSuccess()) {
        return result;
    }
    return loadProgram(program);
}

ExecutionResult ExecutionEngine::initialize() {
    auto result = m_vm->initialize();
    if (result.isSuccess()) {
        m_state = ExecutionState::Initialized;
        // Copy context state?
    }
    return result;
}

ExecutionResult ExecutionEngine::execute() {
    // Delegate to VM
    auto result = m_vm->run();
    if (result.isSuccess()) {
        m_state = ExecutionState::Running;
        // Update state from VM
        auto vmState = m_vm->state();
        if (vmState == VMState::Completed) {
            m_state = ExecutionState::Completed;
        } else if (vmState == VMState::Stopped) {
            m_state = ExecutionState::Stopped;
        } else if (vmState == VMState::Error) {
            m_state = ExecutionState::Error;
        }
    } else {
        m_state = ExecutionState::Error;
    }
    return result;
}

ExecutionResult ExecutionEngine::executeStep() {
    auto result = m_vm->step();
    if (result.isSuccess()) {
        auto vmState = m_vm->state();
        if (vmState == VMState::Completed) {
            m_state = ExecutionState::Completed;
        } else if (vmState == VMState::Running) {
            m_state = ExecutionState::Running;
        } else if (vmState == VMState::Paused) {
            m_state = ExecutionState::Paused;
        } else if (vmState == VMState::Error) {
            m_state = ExecutionState::Error;
        }
    }
    return result;
}

ExecutionResult ExecutionEngine::pause() {
    auto result = m_vm->pause();
    if (result.isSuccess()) {
        m_state = ExecutionState::Paused;
    }
    return result;
}

ExecutionResult ExecutionEngine::resume() {
    auto result = m_vm->resume();
    if (result.isSuccess()) {
        m_state = ExecutionState::Running;
    }
    return result;
}

ExecutionResult ExecutionEngine::stop() {
    auto result = m_vm->stop();
    if (result.isSuccess()) {
        m_state = ExecutionState::Stopped;
    }
    return result;
}

ExecutionState ExecutionEngine::getState() const {
    return m_state;
}

ExecutionResult ExecutionEngine::getLastResult() const {
    return m_lastResult;
}

ExecutionContext& ExecutionEngine::context() {
    return m_vm->context();
}

InstructionDispatcher& ExecutionEngine::dispatcher() {
    return m_dispatcher;
}

RobotApiDispatcher& ExecutionEngine::apiDispatcher() {
    return m_apiDispatcher;
}

RuntimeServices& ExecutionEngine::services() {
    return m_services;
}

Scheduler& ExecutionEngine::scheduler() {
    return m_scheduler;
}

} // namespace execution
} // namespace robot