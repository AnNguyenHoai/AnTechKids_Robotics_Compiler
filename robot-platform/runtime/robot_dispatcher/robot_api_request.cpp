#include "robot_api_request.h"

namespace robot {
namespace execution {

RobotApiRequest::RobotApiRequest()
    : m_apiId(ApiId::UNKNOWN), m_contextId(0),
      m_timestamp(std::chrono::steady_clock::now()) {}

RobotApiRequest::RobotApiRequest(ApiId apiId, const std::vector<RuntimeValue>& params)
    : m_apiId(apiId), m_parameters(params), m_contextId(0),
      m_timestamp(std::chrono::steady_clock::now()) {}

ApiId RobotApiRequest::apiId() const { return m_apiId; }
const std::vector<RuntimeValue>& RobotApiRequest::parameters() const { return m_parameters; }

void RobotApiRequest::setApiId(ApiId id) { m_apiId = id; }
void RobotApiRequest::setParameters(const std::vector<RuntimeValue>& params) { m_parameters = params; }
void RobotApiRequest::addParameter(const RuntimeValue& value) { m_parameters.push_back(value); }

void RobotApiRequest::setExecutionContextId(uint64_t id) { m_contextId = id; }
uint64_t RobotApiRequest::executionContextId() const { return m_contextId; }

void RobotApiRequest::setTimestamp(std::chrono::steady_clock::time_point ts) { m_timestamp = ts; }
std::chrono::steady_clock::time_point RobotApiRequest::timestamp() const { return m_timestamp; }

} // namespace execution
} // namespace robot