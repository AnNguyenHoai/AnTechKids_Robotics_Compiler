# Opcode Reference

This is a complete list of all opcodes used by the Robot VM.

| Opcode | ID | Category | Description |
|--------|----|----------|-------------|
| `Forward` | 2 | motion | Move robot forward |
| `Backward` | 3 | motion | Move robot backward |
| `TurnLeft` | 4 | motion | Rotate robot left |
| `TurnRight` | 5 | motion | Rotate robot right |
| `SetMotorSpeed` | 35 | motion | Set motor speeds independently |
| `Wait` | 7 | system | Wait milliseconds |
| `Stop` | 6 | system | Stop robot |
| `LoadConst` | 1 | internal | Load constant to variable |
| `CompareEQ` | 8 | internal | Compare equal |
| `CompareNE` | 9 | internal | Compare not equal |
| `CompareLT` | 10 | internal | Compare less than |
| `CompareLE` | 11 | internal | Compare less or equal |
| `CompareGT` | 12 | internal | Compare greater than |
| `CompareGE` | 13 | internal | Compare greater or equal |
| `Jump` | 14 | internal | Unconditional jump |
| `JumpIfFalse` | 15 | internal | Jump if false |
| `JumpIfTrue` | 16 | internal | Jump if true |
| `Label` | 17 | internal | Label placeholder |
| `Add` | 20 | internal | Addition |
| `Sub` | 21 | internal | Subtraction |
| `Mul` | 22 | internal | Multiplication |
| `Div` | 23 | internal | Integer division |
| `Mod` | 24 | internal | Modulo |
| `Pow` | 25 | internal | Power (integer exponent) |
| `Neg` | 26 | internal | Negate |
| `Call` | 27 | internal | Call user function |
| `Return` | 28 | internal | Return from function |
| `Store` | 29 | internal | Store value from source to destination variable |
| `ReadUltrasonic` | 30 | sensor | Read ultrasonic distance in cm |
| `ReadTouch` | 31 | sensor | Read touch sensor state (0/1) |
| `ReadLight` | 32 | sensor | Read light sensor raw value (0-1023) |
| `ReadColor` | 33 | sensor | Read color sensor (placeholder) |
| `ReadLine` | 34 | sensor | Read line sensor (0=white, 1=dark) |
| `GetTraceValue` | 42 | sensor | Get trace sensor value (0/50/100 based on line detection) |
| `GetTraceState` | 43 | sensor | Get trace sensor state (boolean) |
| `GetTraceRaw` | 44 | sensor | Get raw bitmask of all 3 trace sensors |
| `SetServo` | 36 | servo | Set servo angle |
| `Set3CLed` | 37 | led | Set 3-color LED state |
| `SetLightSensorLed` | 38 | led | Set light sensor LED state |
| `SetMotorStraightAngle` | 39 | motor | Set motor straight angle |
| `LineBasis` | 47 | line | Basic line following step (adjust motors based on sensor mask) |
| `LineFollow` | 48 | line | Follow line continuously until lost |
| `LineStop` | 49 | line | Stop line following (stop motors) |
| `LineIntersectionStop` | 40 | line | Stop at line intersection |
| `SetMp3Play` | 41 | peripheral | Play MP3 track (adapted to active buzzer beep) |

---
**Note:** Internal opcodes (ID >= 8) are used by the compiler and VM internally, not exposed to users.
