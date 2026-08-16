#pragma once

#include "robot_api_request.h"
#include "robot_api_result.h"
#include "i_robot_api.h"
#include <memory>

namespace robot {
namespace execution {

/**
 * RobotApiMapper – maps ApiId to IRobotApi method calls.
 *
 * This class is responsible for routing requests to the appropriate
 * IRobotApi method. It does NOT execute any logic; it only maps.
 */
class RobotApiMapper {
public:
    explicit RobotApiMapper(std::shared_ptr<IRobotApi> api);

    RobotApiResult map(const RobotApiRequest& request);

private:
    std::shared_ptr<IRobotApi> m_api;
};

} // namespace execution
} // namespace robot