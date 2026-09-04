#pragma once

#include <cstdint>
#include <string>
#include <functional>
#include <unordered_map>
#include <vector>
#include "execution_context.h"
#include "execution_result.h"

namespace robot {
namespace execution {

class RobotAPIDispatcher {
public:
    using APIFunction = std::function<ExecutionResult(ExecutionContext&, const std::string&, const std::vector<int>&)>;

    RobotAPIDispatcher();

    void registerAPI(const std::string& name, APIFunction func);
    ExecutionResult dispatch(ExecutionContext& context, const std::string& name, const std::vector<int>& args);

private:
    std::unordered_map<std::string, APIFunction> m_apis;
};

} // namespace execution
} // namespace robot