#include "robot_api_mapper.h"

namespace robot {
namespace execution {

RobotApiMapper::RobotApiMapper(std::shared_ptr<IRobotApi> api) : m_api(api) {
    if (!m_api) {
        throw std::runtime_error("RobotApiMapper: IRobotApi cannot be null");
    }
}

RobotApiResult RobotApiMapper::map(const RobotApiRequest& request) {
    // Delegate to IRobotApi::dispatch for generic handling.
    // Specific methods could be called based on ApiId, but for now we use generic dispatch.
    return m_api->dispatch(request);
}

} // namespace execution
} // namespace robot