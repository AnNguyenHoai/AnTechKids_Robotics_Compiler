#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include "execution_result.h"

namespace robot {
namespace execution {

// Service interfaces (pure virtual)
class TimerService {
public:
    virtual ~TimerService() = default;
    virtual uint32_t getCurrentTimeMs() = 0;
    virtual void sleepMs(uint32_t ms) = 0;
};

class VariableManager {
public:
    virtual ~VariableManager() = default;
    virtual void setVariable(const std::string& name, int value) = 0;
    virtual int getVariable(const std::string& name) const = 0;
};

class MemoryManager {
public:
    virtual ~MemoryManager() = default;
    // Placeholder
};

class LoaderService {
public:
    virtual ~LoaderService() = default;
    virtual ExecutionResult loadProgram(const std::string& programData) = 0;
};

class FunctionManager {
public:
    virtual ~FunctionManager() = default;
    // Placeholder
};

// Service locator
class ServiceLocator {
public:
    static ServiceLocator& instance();

    void setTimerService(std::unique_ptr<TimerService> service);
    TimerService* getTimerService() const;

    void setVariableManager(std::unique_ptr<VariableManager> manager);
    VariableManager* getVariableManager() const;

    void setMemoryManager(std::unique_ptr<MemoryManager> manager);
    MemoryManager* getMemoryManager() const;

    void setLoaderService(std::unique_ptr<LoaderService> loader);
    LoaderService* getLoaderService() const;

    void setFunctionManager(std::unique_ptr<FunctionManager> manager);
    FunctionManager* getFunctionManager() const;

private:
    ServiceLocator() = default;
    std::unique_ptr<TimerService> m_timer;
    std::unique_ptr<VariableManager> m_variableManager;
    std::unique_ptr<MemoryManager> m_memoryManager;
    std::unique_ptr<LoaderService> m_loader;
    std::unique_ptr<FunctionManager> m_functionManager;
};

// Facade for runtime services
class RuntimeServices {
public:
    RuntimeServices();

    TimerService& timer();
    VariableManager& variables();
    MemoryManager& memory();
    LoaderService& loader();
    FunctionManager& functions();

private:
    // Uses ServiceLocator internally
};

} // namespace execution
} // namespace robot