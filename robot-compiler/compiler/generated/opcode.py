"""
AUTO GENERATED FILE
"""

from enum import IntEnum

class Opcode(IntEnum):
    Forward = 2
    Backward = 3
    TurnLeft = 4
    TurnRight = 5
    SetMotorSpeed = 35
    Wait = 7
    Stop = 6
    LoadConst = 1
    CompareEQ = 8
    CompareNE = 9
    CompareLT = 10
    CompareLE = 11
    CompareGT = 12
    CompareGE = 13
    Jump = 14
    JumpIfFalse = 15
    JumpIfTrue = 16
    Label = 17
    Add = 20
    Sub = 21
    Mul = 22
    Div = 23
    Mod = 24
    Pow = 25
    Neg = 26
    Call = 27
    Return = 28
    Store = 29
    ReadUltrasonic = 30
    ReadTouch = 31
    ReadLight = 32
    ReadColor = 33
    ReadLine = 34
    GetTraceValue = 42
    GetTraceState = 43
    GetTraceRaw = 44
    SetServo = 36
    Set3CLed = 37
    SetLightSensorLed = 38
    SetMotorStraightAngle = 39
    LineBasis = 47
    LineFollow = 48
    LineStop = 49
    LineIntersectionStop = 40
    SetMp3Play = 41
