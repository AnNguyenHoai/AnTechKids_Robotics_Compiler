# Opcode Reference

This is a complete list of all opcodes used by the Robot VM.

| Opcode | ID | Category | Description |
|--------|----|----------|-------------|
| `Forward` | 2 | motion | Move robot forward |
| `Backward` | 3 | motion | Move robot backward |
| `TurnLeft` | 4 | motion | Rotate robot left |
| `TurnRight` | 5 | motion | Rotate robot right |
| `SetMotorSpeed` | 35 | motion | Set motor speeds independently |
| `MoveInitialize` | 52 | motion | Configure drive motors (left/right ports and reverse mode) |
| `MoveRunAngle` | 53 | motion | Move for a specified angle (wheel rotation or chassis turn) |
| `Wait` | 7 | system | Wait milliseconds |
| `Stop` | 6 | system | Stop robot |
| `ReadUltrasonic` | 30 | sensor | Read ultrasonic distance in cm |
| `ReadTouch` | 31 | sensor | Read touch sensor state (0/1) |
| `ReadLight` | 32 | sensor | Read light sensor raw value (0-1023) |
| `ReadColor` | 33 | sensor | Read color sensor (placeholder) |
| `ReadLine` | 34 | sensor | Read line sensor (0=white, 1=dark) |
| `GetTraceValue` | 42 | sensor | Get trace sensor value (0/50/100 based on line detection) |
| `GetTraceState` | 43 | sensor | Get trace sensor state (boolean) |
| `GetTraceRaw` | 44 | sensor | Get raw bitmask of all 3 trace sensors |
| `GetLightSensorData` | 54 | sensor | Read light sensor digital state (0/1) |
| `Set3CLed` | 37 | led | Set 3-color LED state |
| `SetLightSensorLed` | 38 | led | Set light sensor LED state |
| `SetServo` | 36 | servo | Set servo angle |
| `SetSeeringEngine` | 55 | servo | Set steering engine angle |
| `SetSeeringEngineTime` | 56 | servo | Set steering engine angle and hold for time |
| `SetMotor` | 57 | motor | Set speed of a DC motor on given port |
| `SetMotorServo` | 58 | motor | Set motor+servo combination |
| `SetMotorStraightAngle` | 39 | motor | Move both motors for a given angle |
| `LineBasis` | 47 | line | Basic line following step (adjust motors based on sensor mask) |
| `LineFollow` | 48 | line | Follow line continuously until lost |
| `LineStop` | 49 | line | Stop line following (stop motors) |
| `LineMillisecond` | 59 | line | Line follow for a specified time (ms), blocking |
| `LineIntersectionStop` | 40 | line | Follow line until intersection, then stop |
| `LineTurnEncounterLine` | 50 | line | Turn until a line is encountered |
| `LineForBmp` | 51 | line | Follow line for a given degree (time-based) |
| `LineSetInitialize` | 60 | line | Initialize line sensor parameters |
| `SetMp3Play` | 41 | peripheral | Play MP3 track (adapted to active buzzer beep) |
| `SetLizard` | 61 | peripheral | Control peripheral lizard (unknown) |
| `UpdateVar` | 62 | gui | Update variable display in GUI |
| `DisplayVariable` | 63 | gui | Display variable value in GUI |
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
| `Nop` | 64 | internal | No operation (placeholder) |

---
**Note:** Internal opcodes (ID >= 8) are used by the compiler and VM internally, not exposed to users.
