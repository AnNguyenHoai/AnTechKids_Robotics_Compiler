#pragma once

#include "i_robot_api.h"
#include <iostream>

namespace robot {
namespace execution {

class DummyRobotApi : public IRobotApi {
public:
    DummyRobotApi() = default;

    RobotApiResult move(const RobotApiRequest& request) override {
        std::cout << "[DummyRobotApi] move called with apiId=" << static_cast<int>(request.apiId())
                  << " params=" << request.parameters().size() << std::endl;
        return RobotApiResult(PlatformStatus::OK, "Dummy move");
    }

    RobotApiResult stop(const RobotApiRequest& request) override {
        std::cout << "[DummyRobotApi] stop called" << std::endl;
        return RobotApiResult(PlatformStatus::OK, "Dummy stop");
    }

    RobotApiResult wait(const RobotApiRequest& request) override {
        std::cout << "[DummyRobotApi] wait called" << std::endl;
        return RobotApiResult(PlatformStatus::OK, "Dummy wait");
    }

    RobotApiResult setLed(const RobotApiRequest& request) override {
        std::cout << "[DummyRobotApi] setLed called" << std::endl;
        return RobotApiResult(PlatformStatus::OK, "Dummy setLed");
    }

    RobotApiResult readSensor(const RobotApiRequest& request) override {
        std::cout << "[DummyRobotApi] readSensor called" << std::endl;
        return RobotApiResult(PlatformStatus::OK, "Dummy readSensor");
    }

    RobotApiResult playAudio(const RobotApiRequest& request) override {
        std::cout << "[DummyRobotApi] playAudio called" << std::endl;
        return RobotApiResult(PlatformStatus::OK, "Dummy playAudio");
    }

    RobotApiResult dispatch(const RobotApiRequest& request) override {
        std::cout << "[DummyRobotApi] dispatch apiId=" << static_cast<int>(request.apiId()) << std::endl;
        // Route to specific methods based on apiId
        switch (request.apiId()) {
            case ApiId::FORWARD:
            case ApiId::BACKWARD:
            case ApiId::TURN_LEFT:
            case ApiId::TURN_RIGHT:
                return move(request);
            case ApiId::STOP:
                return stop(request);
            case ApiId::WAIT:
                return wait(request);
            case ApiId::SET_LED:
                return setLed(request);
            case ApiId::SET_SPEED:
                // fall through to default OK
            case ApiId::READ_COLOR:
                return readSensor(request); // or specific handler
            default:
                return RobotApiResult(PlatformStatus::OK, "Dummy dispatch OK");
        }
    }
};

} // namespace execution
} // namespace robot