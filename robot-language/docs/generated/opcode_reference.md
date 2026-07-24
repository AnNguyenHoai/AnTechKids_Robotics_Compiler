# Opcode Reference

This is a complete list of all opcodes used by the Robot VM.

| Opcode | ID | Category | Description |
|--------|----|----------|-------------|
| `Forward` | 2 | motion | Move robot forward |
| `Backward` | 3 | motion | Move robot backward |
| `TurnLeft` | 4 | motion | Rotate robot left |
| `TurnRight` | 5 | motion | Rotate robot right |
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

---
**Note:** Internal opcodes (ID >= 8) are used by the compiler and VM internally, not exposed to users.
