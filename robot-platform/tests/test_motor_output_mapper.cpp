#include <assert.h>
#include "../main/src/Services/Robot/MotorOutputMapper.h"

using RobotAPI::MotorOutputMapper;

int main() {
    assert(MotorOutputMapper::map(0, 1.0f, 1.0f, 65) == 0);
    assert(MotorOutputMapper::map(1, 1.0f, 1.0f, 65) >= 65);
    assert(MotorOutputMapper::map(50, 1.0f, 1.0f, 65) > 65);
    assert(MotorOutputMapper::map(100, 1.0f, 1.0f, 65) == 100);
    assert(MotorOutputMapper::map(70, 1.0f, 0.80f, 65) >= 65);
    assert(MotorOutputMapper::map(-50, 1.0f, 1.0f, 65) <= -65);
    return 0;
}
