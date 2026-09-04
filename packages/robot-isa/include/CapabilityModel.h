#pragma once

#include <stdint.h>

struct CapabilityDescriptor
{
    const char* id;
    const char* category;
    const char* description;
    const uint8_t* opcodes;
    uint8_t opcodeCount;
    bool required;
};

namespace CapabilityModel
{
inline constexpr uint8_t MotionBasicOpcodes[] = {2, 3, 4, 5, 6};
inline constexpr uint8_t MotionSpeedOpcodes[] = {35};
inline constexpr uint8_t MotionEncoderAngleOpcodes[] = {52, 53};
inline constexpr uint8_t SensorUltrasonicOpcodes[] = {30};
inline constexpr uint8_t SensorTouchOpcodes[] = {31};
inline constexpr uint8_t SensorLightOpcodes[] = {32, 54};
inline constexpr uint8_t SensorColorOpcodes[] = {33};
inline constexpr uint8_t SensorLineOpcodes[] = {34, 42, 43, 44};
inline constexpr uint8_t ActuatorServoOpcodes[] = {36, 55, 56};
inline constexpr uint8_t ActuatorLedOpcodes[] = {37, 38};
inline constexpr uint8_t ActuatorMotorOpcodes[] = {39, 57, 58};
inline constexpr uint8_t LineFollowOpcodes[] = {40, 47, 48, 49, 50, 51, 59, 60};
inline constexpr uint8_t PeripheralMp3Opcodes[] = {41};
inline constexpr uint8_t PeripheralLizardOpcodes[] = {61};
inline constexpr uint8_t GuiVariableOpcodes[] = {62, 63};
inline constexpr uint8_t RuntimeControlOpcodes[] = {1, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 64};

inline constexpr CapabilityDescriptor All[] = {
    {"motion.basic", "motion", "Basic forward/backward/turn/stop motion", MotionBasicOpcodes, 5, true},
    {"motion.speed", "motion", "Direct motor speed control", MotionSpeedOpcodes, 1, false},
    {"motion.encoder_angle", "motion", "Encoder/angle based movement", MotionEncoderAngleOpcodes, 2, false},
    {"sensor.ultrasonic", "sensor", "Ultrasonic distance sensing", SensorUltrasonicOpcodes, 1, false},
    {"sensor.touch", "sensor", "Touch sensing", SensorTouchOpcodes, 1, false},
    {"sensor.light", "sensor", "Light sensing", SensorLightOpcodes, 2, false},
    {"sensor.color", "sensor", "Color sensing", SensorColorOpcodes, 1, false},
    {"sensor.line", "sensor", "Line sensing and trace state", SensorLineOpcodes, 4, false},
    {"actuator.servo", "actuator", "Servo and steering control", ActuatorServoOpcodes, 3, false},
    {"actuator.led", "actuator", "LED control", ActuatorLedOpcodes, 2, false},
    {"actuator.motor", "actuator", "Motor helper operations", ActuatorMotorOpcodes, 3, false},
    {"line.follow", "line", "Line following services", LineFollowOpcodes, 8, false},
    {"peripheral.mp3", "peripheral", "MP3 playback", PeripheralMp3Opcodes, 1, false},
    {"peripheral.lizard", "peripheral", "Lizard peripheral", PeripheralLizardOpcodes, 1, false},
    {"gui.variable", "gui", "Variable display/update helpers", GuiVariableOpcodes, 2, false},
    {"runtime.control", "runtime", "Values, comparisons, control flow and calls", RuntimeControlOpcodes, 23, true}
};
inline constexpr uint8_t Count = static_cast<uint8_t>(sizeof(All) / sizeof(All[0]));

inline bool supports(const CapabilityDescriptor& capability, uint8_t opcode)
{
    for (uint8_t i = 0; i < capability.opcodeCount; ++i)
    {
        if (capability.opcodes[i] == opcode) return true;
    }
    return false;
}
}
