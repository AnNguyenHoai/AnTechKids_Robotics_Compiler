#include "runtime_services.h"

namespace robot {
namespace execution {

ServiceLocator& ServiceLocator::instance() {
    static ServiceLocator locator;
    return locator;
}

void ServiceLocator::setTimerService(std::unique_ptr<TimerService> service) {
    m_timer = std::move(service);
}

TimerService* ServiceLocator::getTimerService() const {
    return m_timer.get();
}

void ServiceLocator::setVariableManager(std::unique_ptr<VariableManager> manager) {
    m_variableManager = std::move(manager);
}

VariableManager* ServiceLocator::getVariableManager() const {
    return m_variableManager.get();
}

void ServiceLocator::setMemoryManager(std::unique_ptr<MemoryManager> manager) {
    m_memoryManager = std::move(manager);
}

MemoryManager* ServiceLocator::getMemoryManager() const {
    return m_memoryManager.get();
}

void ServiceLocator::setLoaderService(std::unique_ptr<LoaderService> loader) {
    m_loader = std::move(loader);
}

LoaderService* ServiceLocator::getLoaderService() const {
    return m_loader.get();
}

void ServiceLocator::setFunctionManager(std::unique_ptr<FunctionManager> manager) {
    m_functionManager = std::move(manager);
}

FunctionManager* ServiceLocator::getFunctionManager() const {
    return m_functionManager.get();
}

RuntimeServices::RuntimeServices() {
    // Optionally set default stub implementations (currently null)
}

TimerService& RuntimeServices::timer() {
    return *ServiceLocator::instance().getTimerService();
}

VariableManager& RuntimeServices::variables() {
    return *ServiceLocator::instance().getVariableManager();
}

MemoryManager& RuntimeServices::memory() {
    return *ServiceLocator::instance().getMemoryManager();
}

LoaderService& RuntimeServices::loader() {
    return *ServiceLocator::instance().getLoaderService();
}

FunctionManager& RuntimeServices::functions() {
    return *ServiceLocator::instance().getFunctionManager();
}

} // namespace execution
} // namespace robot