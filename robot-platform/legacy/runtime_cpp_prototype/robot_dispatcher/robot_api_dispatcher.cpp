#include "robot_api_dispatcher.h"
#include "execution_types.h"

namespace robot {
namespace execution {

RobotApiDispatcher::RobotApiDispatcher(std::shared_ptr<IRobotApi> robotApi)
    : m_robotApi(robotApi) {
    if (!m_robotApi) {
        throw std::runtime_error("RobotApiDispatcher: IRobotApi cannot be null");
    }
    m_mapper = std::make_unique<RobotApiMapper>(m_robotApi);
}

RobotApiResult RobotApiDispatcher::dispatch(const RobotApiRequest& request) {
    auto validation = validateRequest(request);
    if (validation.status() != PlatformStatus::OK) {
        return validation;
    }
    return m_mapper->map(request);
}

RobotApiResult RobotApiDispatcher::validateRequest(const RobotApiRequest& request) {
    if (request.apiId() == ApiId::UNKNOWN) {
        return RobotApiResult(PlatformStatus::ERROR, "Unknown API ID");
    }
    return RobotApiResult(PlatformStatus::OK);
}

// Helper implementations
RobotApiResult RobotApiDispatcher::move(const std::string& direction, int speed) {
    RobotApiRequest request;
    request.setApiId(ApiId::FORWARD); // just a placeholder; real mapping would distinguish direction
    // In real implementation, we would map direction to appropriate ApiId.
    // For now, we just forward to generic dispatch.
    return dispatch(request);
}

RobotApiResult RobotApiDispatcher::stop() {
    RobotApiRequest request(ApiId::STOP, {});
    return dispatch(request);
}

RobotApiResult RobotApiDispatcher::wait(uint32_t ms) {
    RobotApiRequest request;
    request.setApiId(ApiId::WAIT);
    request.addParameter(RuntimeValue(static_cast<int32_t>(ms)));
    return dispatch(request);
}

RobotApiResult RobotApiDispatcher::setLed(int port, int state) {
    RobotApiRequest request;
    request.setApiId(ApiId::SET_LED);
    request.addParameter(RuntimeValue(port));
    request.addParameter(RuntimeValue(state));
    return dispatch(request);
}

RobotApiResult RobotApiDispatcher::readSensor(int sensorId) {
    RobotApiRequest request;
    // We'll use READ_ULTRASONIC as default; real mapping would use proper ApiId
    request.setApiId(ApiId::READ_ULTRASONIC);
    request.addParameter(RuntimeValue(sensorId));
    return dispatch(request);
}

RobotApiResult RobotApiDispatcher::playAudio(int index) {
    RobotApiRequest request;
    request.setApiId(ApiId::PLAY_BUZZER);
    request.addParameter(RuntimeValue(index));
    return dispatch(request);
}

} // namespace execution
} // namespace robot