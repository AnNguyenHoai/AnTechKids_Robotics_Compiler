#pragma once

#include "runtime_value.h"
#include <string>
#include <cstdint>
#include <optional>
#include <chrono>

namespace robot {
namespace execution {

class RobotApiResponse {
public:
    RobotApiResponse();
    explicit RobotApiResponse(bool success);

    bool success() const;
    void setSuccess(bool success);

    void setReturnValue(const RuntimeValue& value);
    std::optional<RuntimeValue> returnValue() const;

    void setDiagnostic(const std::string& msg);
    std::string diagnostic() const;

    void setExecutionTime(std::chrono::microseconds us);
    std::chrono::microseconds executionTime() const;

private:
    bool m_success;
    std::optional<RuntimeValue> m_returnValue;
    std::string m_diagnostic;
    std::chrono::microseconds m_executionTime;
};

} // namespace execution
} // namespace robot