#pragma once

#include <cstdint>

namespace robot {
namespace execution {

// --------------------------------------------------------------------------
// Execution Status
// --------------------------------------------------------------------------
enum class ExecutionStatus : uint8_t {
    Success,
    Failure,
    Pending,
    Cancelled,
    Error
};

// --------------------------------------------------------------------------
// Execution Layer (for diagnostics)
// --------------------------------------------------------------------------
enum class ExecutionLayer : uint8_t {
    Engine,
    Context,
    Dispatcher,
    RobotAPI,
    Scheduler,
    Services,
    Unknown
};

// --------------------------------------------------------------------------
// Semantic Classification (from language spec)
// --------------------------------------------------------------------------
enum class Semantic : uint8_t {
    Native,
    Rewrite,
    Nop,
    Stub,
    Approximation,
    Dummy,
    Deprecated,
    Unknown
};

// --------------------------------------------------------------------------
// Instruction Category
// --------------------------------------------------------------------------
enum class InstructionCategory : uint8_t {
    Motion,
    Sensor,
    Led,
    Servo,
    Motor,
    Line,
    Peripheral,
    System,
    Gui,
    Internal,
    Unknown
};

// --------------------------------------------------------------------------
// Opcode Enumeration
//
// All opcode values are taken from the official language specification
// (api.yaml) to ensure consistency between compiler and VM.
// Do not change these values without updating the spec.
// --------------------------------------------------------------------------
enum class Opcode : uint32_t {
    // ----- Internal / VM Instructions -----
    LoadConst          = 1,
    CompareEQ          = 8,
    CompareNE          = 9,
    CompareLT          = 10,
    CompareLE          = 11,
    CompareGT          = 12,
    CompareGE          = 13,
    Jump               = 14,
    JumpIfFalse        = 15,
    JumpIfTrue         = 16,
    Label              = 17,
    Add                = 20,
    Sub                = 21,
    Mul                = 22,
    Div                = 23,
    Mod                = 24,
    Pow                = 25,
    Neg                = 26,
    Call               = 27,
    Return             = 28,
    Store              = 29,
    Nop                = 64,

    // ----- Motion -----
    Forward            = 2,
    Backward           = 3,
    TurnLeft           = 4,
    TurnRight          = 5,
    Stop               = 6,
    Wait               = 7,
    SetMotorSpeed      = 35,
    MoveInitialize     = 52,
    MoveRunAngle       = 53,

    // ----- Sensor -----
    ReadUltrasonic     = 30,
    ReadTouch          = 31,
    ReadLight          = 32,
    ReadColor          = 33,
    ReadLine           = 34,
    GetTraceValue      = 42,
    GetTraceState      = 43,
    GetTraceRaw        = 44,
    GetLightSensorData = 54,

    // ----- LED -----
    Set3CLed           = 37,
    SetLightSensorLed  = 38,

    // ----- Servo / Steering -----
    SetServo           = 36,
    SetSeeringEngine   = 55,
    SetSeeringEngineTime = 56,

    // ----- Motor (DC) -----
    SetMotor           = 57,
    SetMotorServo      = 58,
    SetMotorStraightAngle = 39,

    // ----- Line Following -----
    LineBasis          = 47,
    LineFollow         = 48,
    LineStop           = 49,
    LineMillisecond    = 59,
    LineIntersectionStop = 40,
    LineTurnEncounterLine = 50,
    LineForBmp         = 51,
    LineSetInitialize  = 60,

    // ----- Peripheral -----
    SetMp3Play         = 41,
    SetLizard          = 61,

    // ----- GUI (NOP at runtime) -----
    UpdateVar          = 62,
    DisplayVariable    = 63,
};

} // namespace execution
} // namespace robot