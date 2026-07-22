# Opcode Reference

This is a complete list of all opcodes used by the Robot VM.

| Opcode | ID | Category | Description |
|--------|----|----------|-------------|
| `Forward` | 2 | unknown | Move robot forward |
| `Backward` | 3 | unknown | Move robot backward |
| `TurnLeft` | 4 | unknown | Rotate robot left |
| `TurnRight` | 5 | unknown | Rotate robot right |
| `Wait` | 7 | unknown | Wait milliseconds |
| `Stop` | 6 | unknown | Stop robot |
| `LoadConst` | 1 | unknown | Load constant to variable |
| `CompareEQ` | 8 | unknown | Compare equal |
| `CompareNE` | 9 | unknown | Compare not equal |
| `CompareLT` | 10 | unknown | Compare less than |
| `CompareLE` | 11 | unknown | Compare less or equal |
| `CompareGT` | 12 | unknown | Compare greater than |
| `CompareGE` | 13 | unknown | Compare greater or equal |
| `Jump` | 14 | unknown | Unconditional jump |
| `JumpIfFalse` | 15 | unknown | Jump if false |
| `JumpIfTrue` | 16 | unknown | Jump if true |
| `Label` | 17 | unknown | Label placeholder |
| `Add` | 20 | unknown | Addition |
| `Sub` | 21 | unknown | Subtraction |
| `Mul` | 22 | unknown | Multiplication |
| `Div` | 23 | unknown | Integer division |
| `Mod` | 24 | unknown | Modulo |
| `Pow` | 25 | unknown | Power (integer exponent) |
| `Neg` | 26 | unknown | Negate |
| `Call` | 27 | unknown | Call user function |
| `Return` | 28 | unknown | Return from function |
| `Store` | 29 | unknown | Store value from source to destination variable |

---
**Note:** Internal opcodes (ID >= 8) are used by the compiler and VM internally, not exposed to users.
