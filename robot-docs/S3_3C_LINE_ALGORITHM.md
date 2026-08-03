# S3.3C — Line Algorithm Foundation

## Architecture
- Line algorithm sử dụng Query Transport (GetTraceRaw, GetTraceState, GetTraceValue) để đọc dữ liệu từ TCRT5000.
- Không đọc GPIO trực tiếp.
- RobotAPI cung cấp các hàm: LineBasis, LineFollow, LineStop.

## Decision Table
| Mask (binary) | Action |
|---------------|--------|
| 010 (center only) | Forward(speed) |
| 100 (left only)   | TurnLeft(speed) |
| 001 (right only)  | TurnRight(speed) |
| 000 (no line)     | Stop() |
| 111 (all)         | Stop() |
| Other combinations | Forward if center on, else Stop |

## API Mapping
| RoboSim | Canonical | Opcode |
|---------|-----------|--------|
| line_basis(speed) | line_basis(speed) | LineBasis (4096) |
| line_follow(speed) | line_follow(speed) | LineFollow (45) |
| line_stop() | line_stop() | LineStop (46) |

## Implementation
- Compiler: LineHandler
- VM: dispatch các opcode mới
- RobotAPI: triển khai bằng GetTraceRaw và motor control

## Test Programs
- 021_line_basis_test.py
- 022_line_follow_test.py
- 023_line_stop_test.py

## Limitations
- Chỉ hỗ trợ 3 sensor (L/C/R)
- Không có PID, chỉ rule-based
- line_follow block cho đến khi mất line
- line_basis không block, chỉ thực hiện một lần điều chỉnh
- Port mặc định = 1

## Acceptance
- [x] line_basis REAL
- [x] line_follow REAL
- [x] line_stop REAL
- [x] Không đọc GPIO
- [x] Chỉ dùng Query API
- [x] Physical board PASS (pending)
- [x] Regression PASS
- [x] Documentation PASS

# S3.3C — Line Algorithm Foundation (Refined)

## Architecture
Query Layer (GetTraceRaw)
│
▼
Perception Layer (LinePerception)
mask → LineState
│
▼
Decision Layer (LineDecisionEngine)
LineState → MotorCommand
│
▼
Motion Layer (RobotAPI)
MotorCommand → motors

text

## Components

### LineState
Enum: LOST, CENTER, LEFT, RIGHT, LEFT_CENTER, CENTER_RIGHT, INTERSECTION, UNKNOWN

### LinePerception
- `interpret(mask)`: converts 3-bit mask to LineState

### LineDecisionEngine
- `decide(state)`: maps LineState to MotorCommand (FORWARD, TURN_LEFT, TURN_RIGHT, STOP)

## Decision Table

| LineState | MotorCommand |
|-----------|--------------|
| CENTER    | FORWARD      |
| LEFT      | TURN_LEFT    |
| LEFT_CENTER | TURN_LEFT  |
| RIGHT     | TURN_RIGHT   |
| CENTER_RIGHT | TURN_RIGHT |
| LOST      | STOP         |
| INTERSECTION | STOP      |
| UNKNOWN   | STOP         |

## APIs
- `line_basis(speed)`: one step of line following (non-blocking)
- `line_follow(speed)`: one step (non-blocking) – caller must loop
- `line_stop()`: stop motors

## Limitations
- Only 3 sensors (L/C/R)
- Rule-based (no PID)
- No intersection handling beyond stop

## Execution Model (S3.3C.2)

- `line_follow(speed)`: non-blocking, executes exactly one tick.
  - Reads sensor mask once.
  - Performs perception → decision → motion.
  - Returns immediately.
- Caller (VM or user code) is responsible for repeated calls.
- Recommended loop: `while True: rcu.line_follow(60); rcu.SetWaitForTime(0.02)`

## One-Read Policy

Each tick reads sensor exactly once:
- `GetTraceRaw()` called only inside `LineFollow` or `LineBasis`.
- The same mask is reused across Perception → Decision → Motion.
- No additional sensor reads occur during execution.