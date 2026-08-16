#include "robot_api_result.h"

namespace robot {
namespace execution {

RobotApiResult::RobotApiResult()
    : m_status(PlatformStatus::UNKNOWN), m_errorCode(0) {}

RobotApiResult::RobotApiResult(PlatformStatus status, const std::string& diagnostic)
    : m_status(status), m_diagnostic(diagnostic), m_errorCode(0) {}

PlatformStatus RobotApiResult::status() const { return m_status; }
void RobotApiResult::setStatus(PlatformStatus status) { m_status = status; }

std::string RobotApiResult::diagnostic() const { return m_diagnostic; }
void RobotApiResult::setDiagnostic(const std::string& msg) { m_diagnostic = msg; }

uint32_t RobotApiResult::errorCode() const { return m_errorCode; }
void RobotApiResult::setErrorCode(uint32_t code) { m_errorCode = code; }

void RobotApiResult::setReturnValue(const RuntimeValue& value) {
    m_returnValue = value;
}

std::optional<RuntimeValue> RobotApiResult::returnValue() const {
    return m_returnValue;
}

ExecutionResult RobotApiResult::toExecutionResult(uint32_t opcode) const {
    ExecutionStatus status = (m_status == PlatformStatus::OK)
        ? ExecutionStatus::Success
        : ExecutionStatus::Failure;
    return ExecutionResult(
        status,
        m_errorCode,
        m_diagnostic,
        0, // program counter will be filled by caller
        ExecutionLayer::RobotAPI,
        opcode
    );
}

} // namespace execution
} // namespace robot