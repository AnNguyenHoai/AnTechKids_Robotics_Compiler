#pragma once

namespace RobotNetworkService {
void begin();
void update();
bool isReady();
void setUpdateInProgress(bool value);
const char* hostname();
}
