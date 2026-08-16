#include "robot_api_response.h"

namespace robot {
namespace execution {

RobotApiResponse::RobotApiResponse() : m_success(false), m_executionTime(0) {}
RobotApiResponse::RobotApiResponse(bool success) : m_success(success), m_executionTime(0) {}

bool RobotApiResponse::success() const { return m_success; }
void RobotApiResponse::setSuccess(bool success) { m_success = success; }

void RobotApiResponse::setReturnValue(const RuntimeValue& value) { m_returnValue = value; }
std::optional<RuntimeValue> RobotApiResponse::returnValue() const { return m_returnValue; }

void RobotApiResponse::setDiagnostic(const std::string& msg) { m_diagnostic = msg; }
std::string RobotApiResponse::diagnostic() const { return m_diagnostic; }

void RobotApiResponse::setExecutionTime(std::chrono::microseconds us) { m_executionTime = us; }
std::chrono::microseconds RobotApiResponse::executionTime() const { return m_executionTime; }

} // namespace execution
} // namespace robot