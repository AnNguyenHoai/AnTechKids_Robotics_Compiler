#include "esp32_robot_api.h"

// Include RobotAPI (firmware HAL wrapper)
#include "../../../main/src/Services/Robot/RobotAPI.h"

#include <cstdint>
#include <string>

namespace robot {
namespace execution {

// Helper: extract integer parameter safely
static int32_t getIntParam(const RobotApiRequest& request, size_t index, int32_t defaultValue = 0) {
    if (index < request.parameters().size()) {
        const auto& val = request.parameters()[index];
        if (val.isInteger()) {
            return val.asInteger();
        }
    }
    return defaultValue;
}

// Helper: extract boolean parameter (treat non-zero as true)
static bool getBoolParam(const RobotApiRequest& request, size_t index, bool defaultValue = false) {
    if (index < request.parameters().size()) {
        const auto& val = request.parameters()[index];
        if (val.isBoolean()) {
            return val.asBoolean();
        }
        if (val.isInteger()) {
            return val.asInteger() != 0;
        }
    }
    return defaultValue;
}

RobotApiResult ESP32RobotApi::move(const RobotApiRequest& request) {
    // The move() method is not used directly – dispatch() handles all.
    // Forward to dispatch for consistency.
    return dispatch(request);
}

RobotApiResult ESP32RobotApi::stop(const RobotApiRequest& request) {
    return dispatch(request);
}

RobotApiResult ESP32RobotApi::wait(const RobotApiRequest& request) {
    return dispatch(request);
}

RobotApiResult ESP32RobotApi::setLed(const RobotApiRequest& request) {
    return dispatch(request);
}

RobotApiResult ESP32RobotApi::readSensor(const RobotApiRequest& request) {
    return dispatch(request);
}

RobotApiResult ESP32RobotApi::playAudio(const RobotApiRequest& request) {
    return dispatch(request);
}

RobotApiResult ESP32RobotApi::dispatch(const RobotApiRequest& request) {
    ApiId api = request.apiId();

    switch (api) {
        // ----- Motion -----
        case ApiId::FORWARD: {
            int speed = getIntParam(request, 0, 0);
            RobotAPI::Forward(static_cast<int16_t>(speed));
            return RobotApiResult(PlatformStatus::OK, "Forward " + std::to_string(speed));
        }

        case ApiId::BACKWARD: {
            int speed = getIntParam(request, 0, 0);
            RobotAPI::Backward(static_cast<int16_t>(speed));
            return RobotApiResult(PlatformStatus::OK, "Backward " + std::to_string(speed));
        }

        case ApiId::TURN_LEFT: {
            int speed = getIntParam(request, 0, 0);
            RobotAPI::TurnLeft(static_cast<int16_t>(speed));
            return RobotApiResult(PlatformStatus::OK, "TurnLeft " + std::to_string(speed));
        }

        case ApiId::TURN_RIGHT: {
            int speed = getIntParam(request, 0, 0);
            RobotAPI::TurnRight(static_cast<int16_t>(speed));
            return RobotApiResult(PlatformStatus::OK, "TurnRight " + std::to_string(speed));
        }

        case ApiId::STOP: {
            RobotAPI::Stop();
            return RobotApiResult(PlatformStatus::OK, "Stop");
        }

        case ApiId::WAIT: {
            uint32_t ms = static_cast<uint32_t>(getIntParam(request, 0, 0));
            RobotAPI::Wait(ms);
            return RobotApiResult(PlatformStatus::OK, "Wait " + std::to_string(ms) + " ms");
        }

        // ----- Output: LED -----
        case ApiId::SET_LED: {
            int port = getIntParam(request, 0, 1);
            int state = getIntParam(request, 1, 0);
            RobotAPI::Set3CLed(port, state);
            return RobotApiResult(PlatformStatus::OK, "SetLED port=" + std::to_string(port) + " state=" + std::to_string(state));
        }

        // ----- Audio -----
        case ApiId::PLAY_BUZZER: {
            int index = getIntParam(request, 0, 1);
            RobotAPI::SetMp3Play(index);
            return RobotApiResult(PlatformStatus::OK, "PlayBuzzer index=" + std::to_string(index));
        }

        // ----- Sensors -----
        case ApiId::READ_ULTRASONIC: {
            int16_t distance = RobotAPI::ReadUltrasonic();
            RobotApiResult result(PlatformStatus::OK, "Ultrasonic = " + std::to_string(distance));
            result.setReturnValue(RuntimeValue(static_cast<int32_t>(distance)));
            return result;
        }

        case ApiId::READ_TOUCH: {
            int port = getIntParam(request, 0, 0);
            int16_t value = RobotAPI::ReadTouch(port);
            RobotApiResult result(PlatformStatus::OK, "Touch port " + std::to_string(port) + " = " + std::to_string(value));
            result.setReturnValue(RuntimeValue(static_cast<int32_t>(value)));
            return result;
        }

        case ApiId::READ_LIGHT: {
            int channel = getIntParam(request, 0, 0);
            int16_t value = RobotAPI::ReadLight(channel);
            RobotApiResult result(PlatformStatus::OK, "Light channel " + std::to_string(channel) + " = " + std::to_string(value));
            result.setReturnValue(RuntimeValue(static_cast<int32_t>(value)));
            return result;
        }

        case ApiId::READ_LINE: {
            int channel = getIntParam(request, 0, 0);
            int16_t value = RobotAPI::ReadLine(channel);
            RobotApiResult result(PlatformStatus::OK, "Line channel " + std::to_string(channel) + " = " + std::to_string(value));
            result.setReturnValue(RuntimeValue(static_cast<int32_t>(value)));
            return result;
        }

        case ApiId::READ_COLOR: {
            int16_t value = RobotAPI::ReadColor();
            RobotApiResult result(PlatformStatus::OK, "Color = " + std::to_string(value));
            result.setReturnValue(RuntimeValue(static_cast<int32_t>(value)));
            return result;
        }

        default:
            return RobotApiResult(PlatformStatus::ERROR, "Unknown ApiId: " + std::to_string(static_cast<uint32_t>(api)));
    }
}

} // namespace execution
} // namespace robot