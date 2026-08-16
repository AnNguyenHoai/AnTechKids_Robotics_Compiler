#pragma once

#include "robot_api_request.h"
#include "robot_api_response.h"
#include "robot_api_result.h"

namespace robot {
namespace execution {

/**
 * IRobotApi – Platform Boundary Interface.
 *
 * This is the ONLY interface through which Runtime communicates with RobotAPI.
 * All hardware-specific details are hidden behind this interface.
 */
class IRobotApi {
public:
    virtual ~IRobotApi() = default;

    // Core API methods (dummy for now)
    virtual RobotApiResult move(const RobotApiRequest& request) = 0;
    virtual RobotApiResult stop(const RobotApiRequest& request) = 0;
    virtual RobotApiResult wait(const RobotApiRequest& request) = 0;
    virtual RobotApiResult setLed(const RobotApiRequest& request) = 0;
    virtual RobotApiResult readSensor(const RobotApiRequest& request) = 0;
    virtual RobotApiResult playAudio(const RobotApiRequest& request) = 0;

    // Generic dispatch (used by mapper)
    virtual RobotApiResult dispatch(const RobotApiRequest& request) = 0;
};

} // namespace execution
} // namespace robot