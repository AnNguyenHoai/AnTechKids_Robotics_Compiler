#pragma once

#include "robot_api_request.h"
#include "robot_api_response.h"
#include "robot_api_result.h"
#include "robot_api_mapper.h"
#include <memory>

namespace robot {
namespace execution {

/**
 * RobotApiDispatcher – Runtime Platform Boundary.
 *
 * Receives RobotApiRequest, validates, maps to IRobotApi,
 * invokes, and returns RobotApiResult.
 *
 * No hardware access; only routing and error conversion.
 */
class RobotApiDispatcher {
public:
    explicit RobotApiDispatcher(std::shared_ptr<IRobotApi> robotApi);

    // Main entry point
    RobotApiResult dispatch(const RobotApiRequest& request);

    // Helper for common APIs
    RobotApiResult move(const std::string& direction, int speed);
    RobotApiResult stop();
    RobotApiResult wait(uint32_t ms);
    RobotApiResult setLed(int port, int state);
    RobotApiResult readSensor(int sensorId);
    RobotApiResult playAudio(int index);

private:
    std::shared_ptr<IRobotApi> m_robotApi;
    std::unique_ptr<RobotApiMapper> m_mapper;

    RobotApiResult validateRequest(const RobotApiRequest& request);
};

} // namespace execution
} // namespace robot