#pragma once

#include "runtime_value.h"
#include <vector>
#include <cstdint>
#include <string>
#include <chrono>

namespace robot {
namespace execution {

enum class ApiId : uint32_t {
    UNKNOWN = 0,
    FORWARD = 1,
    BACKWARD = 2,
    TURN_LEFT = 3,
    TURN_RIGHT = 4,
    STOP = 5,
    WAIT = 6,
    SET_LED = 7,
    READ_ULTRASONIC = 8,
    READ_TOUCH = 9,
    READ_LIGHT = 10,
    READ_LINE = 11,
    PLAY_BUZZER = 12,
    READ_COLOR = 13, 
};

class RobotApiRequest {
public:
    RobotApiRequest();
    RobotApiRequest(ApiId apiId, const std::vector<RuntimeValue>& params);

    ApiId apiId() const;
    const std::vector<RuntimeValue>& parameters() const;
    void setApiId(ApiId id);
    void setParameters(const std::vector<RuntimeValue>& params);
    void addParameter(const RuntimeValue& value);

    // Optional context
    void setExecutionContextId(uint64_t id);
    uint64_t executionContextId() const;

    void setTimestamp(std::chrono::steady_clock::time_point ts);
    std::chrono::steady_clock::time_point timestamp() const;

private:
    ApiId m_apiId;
    std::vector<RuntimeValue> m_parameters;
    uint64_t m_contextId;
    std::chrono::steady_clock::time_point m_timestamp;
};

} // namespace execution
} // namespace robot