#include "RobotHealthPlatform.h"

#include "RobotHealthPlatformSource.h"

RobotHealthService& systemRobotHealth() {
    static RobotHealthPlatformSource source;
    static RobotHealthService service(source);
    return service;
}
