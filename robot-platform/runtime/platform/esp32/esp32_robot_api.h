#pragma once

#include "../../robot_dispatcher/i_robot_api.h"
#include "../../robot_dispatcher/robot_api_request.h"
#include "../../robot_dispatcher/robot_api_result.h"

namespace robot {
namespace execution {

/**
 * ESP32RobotApi – concrete implementation of IRobotApi for ESP32 hardware.
 *
 * All calls are forwarded to the existing RobotAPI namespace which
 * directly interfaces with the HAL (GPIO, PWM, sensors, etc.).
 */
class ESP32RobotApi : public IRobotApi {
public:
    ESP32RobotApi() = default;
    ~ESP32RobotApi() override = default;

    // IRobotApi interface
    RobotApiResult move(const RobotApiRequest& request) override;
    RobotApiResult stop(const RobotApiRequest& request) override;
    RobotApiResult wait(const RobotApiRequest& request) override;
    RobotApiResult setLed(const RobotApiRequest& request) override;
    RobotApiResult readSensor(const RobotApiRequest& request) override;
    RobotApiResult playAudio(const RobotApiRequest& request) override;

    // Generic dispatch – routes to specific methods based on ApiId
    RobotApiResult dispatch(const RobotApiRequest& request) override;
};

} // namespace execution
} // namespace robot