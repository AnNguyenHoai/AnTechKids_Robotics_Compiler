#include "robot_api_dispatcher.h"

namespace robot {
namespace execution {

RobotAPIDispatcher::RobotAPIDispatcher() {
    // Stub
}

void RobotAPIDispatcher::registerAPI(const std::string& name, APIFunction func) {
    m_apis[name] = func;
}

ExecutionResult RobotAPIDispatcher::dispatch(ExecutionContext& context, const std::string& name, const std::vector<int>& args) {
    auto it = m_apis.find(name);
    if (it != m_apis.end()) {
        return it->second(context, name, args);
    }
    return ExecutionResult(true, 0, "RobotAPI not implemented (stub)");
}

} // namespace execution
} // namespace robot