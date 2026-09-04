#pragma once
#include <cstdint>

// AUTO-GENERATED FROM packages/robot-isa/canonical_isa.json.
// This is an adapter boundary; do not define ISA semantics here.
namespace robot_isa {

enum class CanonicalOpcode : uint8_t {
    Invalid = 0xFF,
    MotionForward = 0,
    MotionBackward = 1,
    MotionTurnLeft = 2,
    MotionTurnRight = 3,
    MotionSetMotorSpeed = 4,
    MotionMoveInitialize = 5,
    MotionMoveRunAngle = 6,
    SystemWait = 7,
    SystemStop = 8,
    SensorReadUltrasonic = 9,
    SensorReadTouch = 10,
    SensorReadLight = 11,
    SensorReadColor = 12,
    SensorReadLine = 13,
    SensorGetTraceValue = 14,
    SensorGetTraceState = 15,
    SensorGetTraceRaw = 16,
    SensorGetLightSensorData = 17,
    LedSet3cLed = 18,
    LedSetLightSensorLed = 19,
    ServoSetServo = 20,
    ServoSetSteeringEngine = 21,
    ServoSetSteeringEngineTime = 22,
    MotorSetMotor = 23,
    MotorSetMotorServo = 24,
    MotorSetMotorStraightAngle = 25,
    LineLineBasis = 26,
    LineLineFollow = 27,
    LineLineStop = 28,
    LineLineMillisecond = 29,
    LineLineIntersectionStop = 30,
    LineLineTurnEncounterLine = 31,
    LineLineForBmp = 32,
    LineLineSetInitialize = 33,
    PeripheralSetMp3Play = 34,
    PeripheralSetLizard = 35,
    GuiUpdateVar = 36,
    GuiDisplayVariable = 37,
    ValueLoadConst = 38,
    ControlCompareEq = 39,
    ControlCompareNe = 40,
    ControlCompareLt = 41,
    ControlCompareLe = 42,
    ControlCompareGt = 43,
    ControlCompareGe = 44,
    ControlJump = 45,
    ControlJumpIfFalse = 46,
    ControlJumpIfTrue = 47,
    ControlLabel = 48,
    MathAdd = 49,
    MathSub = 50,
    MathMul = 51,
    MathDiv = 52,
    MathMod = 53,
    MathPow = 54,
    MathNeg = 55,
    RuntimeCall = 56,
    RuntimeReturn = 57,
    ValueStore = 58,
    RuntimeNop = 59,
};

constexpr CanonicalOpcode fromCurrentWireCode(uint8_t code) {
    switch (code) {
        case 2: return CanonicalOpcode::MotionForward;
        case 3: return CanonicalOpcode::MotionBackward;
        case 4: return CanonicalOpcode::MotionTurnLeft;
        case 5: return CanonicalOpcode::MotionTurnRight;
        case 35: return CanonicalOpcode::MotionSetMotorSpeed;
        case 52: return CanonicalOpcode::MotionMoveInitialize;
        case 53: return CanonicalOpcode::MotionMoveRunAngle;
        case 7: return CanonicalOpcode::SystemWait;
        case 6: return CanonicalOpcode::SystemStop;
        case 30: return CanonicalOpcode::SensorReadUltrasonic;
        case 31: return CanonicalOpcode::SensorReadTouch;
        case 32: return CanonicalOpcode::SensorReadLight;
        case 33: return CanonicalOpcode::SensorReadColor;
        case 34: return CanonicalOpcode::SensorReadLine;
        case 42: return CanonicalOpcode::SensorGetTraceValue;
        case 43: return CanonicalOpcode::SensorGetTraceState;
        case 44: return CanonicalOpcode::SensorGetTraceRaw;
        case 54: return CanonicalOpcode::SensorGetLightSensorData;
        case 37: return CanonicalOpcode::LedSet3cLed;
        case 38: return CanonicalOpcode::LedSetLightSensorLed;
        case 36: return CanonicalOpcode::ServoSetServo;
        case 55: return CanonicalOpcode::ServoSetSteeringEngine;
        case 56: return CanonicalOpcode::ServoSetSteeringEngineTime;
        case 57: return CanonicalOpcode::MotorSetMotor;
        case 58: return CanonicalOpcode::MotorSetMotorServo;
        case 39: return CanonicalOpcode::MotorSetMotorStraightAngle;
        case 47: return CanonicalOpcode::LineLineBasis;
        case 48: return CanonicalOpcode::LineLineFollow;
        case 49: return CanonicalOpcode::LineLineStop;
        case 59: return CanonicalOpcode::LineLineMillisecond;
        case 40: return CanonicalOpcode::LineLineIntersectionStop;
        case 50: return CanonicalOpcode::LineLineTurnEncounterLine;
        case 51: return CanonicalOpcode::LineLineForBmp;
        case 60: return CanonicalOpcode::LineLineSetInitialize;
        case 41: return CanonicalOpcode::PeripheralSetMp3Play;
        case 61: return CanonicalOpcode::PeripheralSetLizard;
        case 62: return CanonicalOpcode::GuiUpdateVar;
        case 63: return CanonicalOpcode::GuiDisplayVariable;
        case 1: return CanonicalOpcode::ValueLoadConst;
        case 8: return CanonicalOpcode::ControlCompareEq;
        case 9: return CanonicalOpcode::ControlCompareNe;
        case 10: return CanonicalOpcode::ControlCompareLt;
        case 11: return CanonicalOpcode::ControlCompareLe;
        case 12: return CanonicalOpcode::ControlCompareGt;
        case 13: return CanonicalOpcode::ControlCompareGe;
        case 14: return CanonicalOpcode::ControlJump;
        case 15: return CanonicalOpcode::ControlJumpIfFalse;
        case 16: return CanonicalOpcode::ControlJumpIfTrue;
        case 17: return CanonicalOpcode::ControlLabel;
        case 20: return CanonicalOpcode::MathAdd;
        case 21: return CanonicalOpcode::MathSub;
        case 22: return CanonicalOpcode::MathMul;
        case 23: return CanonicalOpcode::MathDiv;
        case 24: return CanonicalOpcode::MathMod;
        case 25: return CanonicalOpcode::MathPow;
        case 26: return CanonicalOpcode::MathNeg;
        case 27: return CanonicalOpcode::RuntimeCall;
        case 28: return CanonicalOpcode::RuntimeReturn;
        case 29: return CanonicalOpcode::ValueStore;
        case 64: return CanonicalOpcode::RuntimeNop;
        default: return CanonicalOpcode::Invalid;
    }
}

constexpr bool isKnownCurrentWireCode(uint8_t code) {
    return fromCurrentWireCode(code) != CanonicalOpcode::Invalid;
}

} // namespace robot_isa
