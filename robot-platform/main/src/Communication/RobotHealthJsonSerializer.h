#pragma once

#include <string>

#include "../Health/RobotHealth.h"

struct RobotHealthCompatibilityFields {
    bool ready = false;
    bool robotReady = false;
    bool networkReady = false;
    bool otaReady = false;
    bool httpOtaAvailable = true;
    const char* hostname = "";
};

class RobotHealthJsonSerializer {
public:
    static std::string serialize(
        const RobotHealth& health,
        const RobotHealthCompatibilityFields& compatibility
    );

private:
    static std::string escape(const char* value);
    static const char* boolText(bool value) { return value ? "true" : "false"; }
};
