#pragma once

#include "execution_types.h"
#include <string>
#include <cstdint>
#include <optional>
#include "runtime_value.h"   // thêm include

namespace robot {
namespace execution {

enum class PlatformStatus : uint8_t {
    OK,
    ERROR,
    UNSUPPORTED,
    TIMEOUT,
    BUSY,
    UNKNOWN
};

class RobotApiResult {
public:
    RobotApiResult();
    RobotApiResult(PlatformStatus status, const std::string& diagnostic = "");

    PlatformStatus status() const;
    void setStatus(PlatformStatus status);

    std::string diagnostic() const;
    void setDiagnostic(const std::string& msg);

    uint32_t errorCode() const;
    void setErrorCode(uint32_t code);

    // --- Return value support ---
    void setReturnValue(const RuntimeValue& value);
    std::optional<RuntimeValue> returnValue() const;

    // Convert to ExecutionResult
    ExecutionResult toExecutionResult(uint32_t opcode = 0) const;

private:
    PlatformStatus m_status;
    std::string m_diagnostic;
    uint32_t m_errorCode;
    std::optional<RuntimeValue> m_returnValue;   // thêm
};

} // namespace execution
} // namespace robot