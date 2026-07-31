# RoboSim API Capability Matrix — RC1

**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Draft for Review  

---

## Legend

| Column | Description |
|--------|-------------|
| **API** | RoboSim function name |
| **Signature** | Parameters and return type |
| **Semantics Known** | Yes / No / Partial |
| **Category** | `HARDWARE_PRIMITIVE`, `ACTUATOR_PRIMITIVE`, `BEHAVIOR`, `RUNTIME`, `LANGUAGE_FEATURE` |
| **Adapter** | Does `robot-frontend-robosim` transform this? |
| **Compiler** | Does compiler recognize it? (Opcode / function_registry) |
| **VM** | Is there a bytecode handler? |
| **RobotAPI** | Is there a C++ function? |
| **Framework/Service** | Is there a lower‑level service? |
| **HAL** | Does it use HAL? |
| **Hardware** | Physical mapping |
| **Compatibility** | `FULL`, `ADAPTED`, `UNSUPPORTED`, `UNKNOWN` |

---

## Light Sensor APIs

### `GetLightSensorData(port)`

| Field | Value |
|-------|-------|
| Signature | `int GetLightSensorData(int port)` |
| Semantics Known | **Partial** — likely returns digital state (0/1) from a light sensor (e.g., TCRT5000 used as light sensor). Port = pin/channel. |
| Category | `HARDWARE_PRIMITIVE` |
| Adapter | **UNSUPPORTED** — not in `mapping.py` |
| Compiler | **UNSUPPORTED** — not in `function_registry.py` |
| VM | **UNSUPPORTED** — no opcode |
| RobotAPI | **UNSUPPORTED** — no function |
| Framework/Service | Not applicable |
| HAL | Not applicable |
| Hardware | TCRT5000 digital output (0/1) |
| Compatibility | `UNSUPPORTED` |

**Evidence:** Not present in `robot-frontend-robosim/frontend/mapping.py`.  
**Confidence:** HIGH.

---

### `GetLightSensor(port)`

| Field | Value |
|-------|-------|
| Signature | `int GetLightSensor(int port)` |
| Semantics Known | **Partial** — likely analog/raw value from a light sensor (0–1023 or 0–4095). |
| Category | `HARDWARE_PRIMITIVE` |
| Adapter | **SUPPORTED** — maps to `read_light(port)` (in `mapping.py`) |
| Compiler | **SUPPORTED** — `ReadLight` opcode exists |
| VM | **SUPPORTED** — handler for `ReadLight` exists |
| RobotAPI | **SUPPORTED** — `ReadLight(int channel)` exists |
| Framework/Service | Uses `LightSensor` driver (not yet refactored to Sensor Framework) |
| HAL | Not yet; uses `analogRead()` directly |
| Hardware | Analog light sensor / photoresistor |
| Compatibility | `ADAPTED` (mapped to `read_light`) |

**Evidence:** Present in `mapping.py` and `function_registry.py`.  
**Confidence:** HIGH.

**Note for RC1:** The acceptance program uses `GetLightSensorData(1)` and `GetLightSensor(1)`. The latter is supported, the former is not.

---

## Patrol (Trace) APIs

### `GetTraceV2I2CState(port, channel)`

| Field | Value |
|-------|-------|
| Signature | `int GetTraceV2I2CState(int port, int channel)` |
| Semantics Known | **Unknown** — likely returns a boolean/status for a specific channel. Might indicate line detected (black). |
| Category | `HARDWARE_PRIMITIVE` |
| Adapter | **UNSUPPORTED** — not in `mapping.py` |
| Compiler | **UNSUPPORTED** |
| VM | **UNSUPPORTED** |
| RobotAPI | **UNSUPPORTED** |
| Framework/Service | Not applicable |
| HAL | Not applicable |
| Hardware | TCRT5000 (digital) |
| Compatibility | `UNSUPPORTED` |

**Evidence:** Not in mapping.  
**Confidence:** HIGH.

---

### `GetTraceV2I2C(port, channel)`

| Field | Value |
|-------|-------|
| Signature | `int GetTraceV2I2C(int port, int channel)` |
| Semantics Known | **Unknown** — might return raw value (analog) or position index for 8‑eye array. |
| Category | `HARDWARE_PRIMITIVE` |
| Adapter | **UNSUPPORTED** |
| Compiler | **UNSUPPORTED** |
| VM | **UNSUPPORTED** |
| RobotAPI | **UNSUPPORTED** |
| Framework/Service | Not applicable |
| HAL | Not applicable |
| Hardware | Likely TCRT5000 (analog if available) |
| Compatibility | `UNSUPPORTED` |

**Evidence:** Not in mapping.  
**Confidence:** HIGH.

---

### `GetTraceV2I2CChxState(port, channel)`

| Field | Value |
|-------|-------|
| Signature | `int GetTraceV2I2CChxState(int port, int channel)` |
| Semantics Known | **Yes** — returns digital state (0/1) for a given channel of the trace sensor array. |
| Category | `HARDWARE_PRIMITIVE` |
| Adapter | **SUPPORTED** — maps to `read_line(channel)` (drops `port` argument, keeps `channel`) |
| Compiler | **SUPPORTED** — `ReadLine` opcode |
| VM | **SUPPORTED** — `ReadLine` handler |
| RobotAPI | **SUPPORTED** — `ReadLine(int channel)` |
| Framework/Service | Uses `TCRT5000` driver via SensorManager |
| HAL | **YES** — uses `GPIOHal` |
| Hardware | TCRT5000 digital pin (line_left, center, right) |
| Compatibility | `ADAPTED` (port → ignored, channel → 0..2 for L/C/R) |

**Evidence:** In `mapping.py`:  
```python
"GetTraceV2I2CChxState": {
    "target": "read_line",
    "arg_indices": [1],
    "expected_args": 2,
}
Confidence: HIGH.

Note: The RC1 program calls GetTraceV2I2CChxState(1, 1), which adapts to read_line(1) → center line sensor.

Motion APIs
SetMoveSpeed(left, right)
Field	Value
Signature	void SetMoveSpeed(int left, int right)
Semantics Known	Yes — sets motor speeds directly. Left and right values typically -100..100.
Category	ACTUATOR_PRIMITIVE
Adapter	UNSUPPORTED — not mapped
Compiler	UNSUPPORTED — no opcode
VM	UNSUPPORTED
RobotAPI	UNSUPPORTED — but setMotorsDirect(left, right) exists as internal function.
Framework/Service	Motion service (Motor)
HAL	YES — uses PWM via HAL
Hardware	DC motors
Compatibility	UNSUPPORTED (can be added easily via opcode)
Evidence: Not in mapping. RobotAPI::setMotorsDirect() exists but not exposed to VM.
Confidence: HIGH.

SetMoveRunSecond(direction, speed, seconds)
Field	Value
Signature	void SetMoveRunSecond(string direction, int speed, float seconds)
Semantics Known	Yes — move in given direction for specified seconds, then stop. Blocking.
Category	ACTUATOR_PRIMITIVE
Adapter	SUPPORTED — transforms to forward(speed); wait(seconds*1000); stop()
Compiler	SUPPORTED — compiles to Forward, Wait, Stop opcodes
VM	SUPPORTED — handles those opcodes
RobotAPI	SUPPORTED — Forward, Wait, Stop
Framework/Service	Motion controller
HAL	YES
Hardware	DC motors
Compatibility	FULL
Evidence: Present in RoboSimTransformer._handle_move_run_second().
Confidence: HIGH.

SetMoveRunAngle(direction, speed, angle)
Field	Value
Signature	void SetMoveRunAngle(string direction, int speed, int angle)
Semantics Known	Partial — likely moves for a specified angle (degrees) based on encoder or timing. Blocking? Unknown.
Category	ACTUATOR_PRIMITIVE
Adapter	UNSUPPORTED — not mapped
Compiler	UNSUPPORTED
VM	UNSUPPORTED
RobotAPI	UNSUPPORTED
Framework/Service	Not applicable (no encoder)
HAL	Not applicable
Hardware	DC motors + encoders (if available)
Compatibility	UNSUPPORTED (requires encoder support)
Evidence: Not in mapping. No encoder support in current hardware.
Confidence: HIGH.

Line Behavior APIs
All line_* APIs are BEHAVIOR‑level functions. They are not hardware primitives.

line_set_initialize(port, color, chassisType)
Field	Value
Signature	void line_set_initialize(int port, string color, string chassisType)
Semantics Known	Unknown — likely configures line following parameters (port, line color, chassis type).
Category	BEHAVIOR
Adapter	UNSUPPORTED
Compiler	UNSUPPORTED
VM	UNSUPPORTED
RobotAPI	UNSUPPORTED
Framework/Service	Not implemented
HAL	Not applicable
Hardware	None directly
Compatibility	UNKNOWN
Evidence: Not in any mapping; semantics need reverse‑engineering.
Confidence: LOW.

line_basis(speed)
Field	Value
Signature	void line_basis(int speed)
Semantics Known	Unknown — likely starts basic line following at given speed. Blocking.
Category	BEHAVIOR
Adapter	UNSUPPORTED
Compiler	UNSUPPORTED
VM	UNSUPPORTED
RobotAPI	UNSUPPORTED
Framework/Service	Not implemented
HAL	Not applicable
Hardware	Motors + line sensors
Compatibility	UNKNOWN
Evidence: Not in mapping.
Confidence: LOW.

line_intersection_stop(speed, type)
Field	Value
Signature	void line_intersection_stop(int speed, int type)
Semantics Known	Unknown — likely follows line until an intersection of given type is detected, then stops. Blocking.
Category	BEHAVIOR
Adapter	UNSUPPORTED
Compiler	UNSUPPORTED
VM	UNSUPPORTED
RobotAPI	UNSUPPORTED
Framework/Service	Not implemented
HAL	Not applicable
Hardware	Motors + line sensors
Compatibility	UNKNOWN
Evidence: Not in mapping.
Confidence: LOW.

line_turn_encounterline(speed, angle, direction)
Field	Value
Signature	void line_turn_encounterline(int speed, int angle, int direction)
Semantics Known	Unknown — likely turns a given angle until a line is encountered. Blocking.
Category	BEHAVIOR
Adapter	UNSUPPORTED
Compiler	UNSUPPORTED
VM	UNSUPPORTED
RobotAPI	UNSUPPORTED
Framework/Service	Not implemented
HAL	Not applicable
Hardware	Motors + line sensors (no encoder)
Compatibility	UNKNOWN
Evidence: Not in mapping.
Confidence: LOW.

line_for_bmp(speed, degree)
Field	Value
Signature	void line_for_bmp(int speed, int degree)
Semantics Known	Unknown — likely follows a bitmap pattern? May be related to black‑line tracing for a certain angle.
Category	BEHAVIOR
Adapter	UNSUPPORTED
Compiler	UNSUPPORTED
VM	UNSUPPORTED
RobotAPI	UNSUPPORTED
Framework/Service	Not implemented
HAL	Not applicable
Hardware	Motors + line sensors
Compatibility	UNKNOWN
Evidence: Not in mapping.
Confidence: LOW.

Runtime / Thread APIs
_thread.start_new_thread(func, ())
Field	Value
Signature	void _thread.start_new_thread(function, tuple)
Semantics Known	Yes — spawns a new concurrent thread executing the given function.
Category	RUNTIME
Adapter	SUPPORTED — transforms to direct function call (since VM has no threading)
Compiler	SUPPORTED — currently rewrites to a direct call (no threading)
VM	PARTIAL — the compiler currently inlines the function body; no actual threading
RobotAPI	Not applicable
Framework/Service	Not applicable
HAL	Not applicable
Hardware	Not applicable
Compatibility	ADAPTED (no real threading; inlined)
Evidence: In RoboSimTransformer._handle_thread_start(), it replaces _thread.start_new_thread(task, ()) with task().
Confidence: HIGH.

Gap: Current VM is single‑threaded; multiple _thread.start_new_thread calls are inlined sequentially. For RC1 with two tasks, they will run sequentially, not concurrently.

Language Features
Feature	Support	Notes
while True	SUPPORTED	Compiles to infinite loop (jump)
while 1	SUPPORTED	Same as while True
if / else	SUPPORTED	Nested if works
global	PARTIAL	Variables are global by default; global keyword ignored
Function definitions	SUPPORTED	User functions compiled
Function calls	SUPPORTED	Inlined
Nested if	SUPPORTED	Compiled correctly
Multiple tasks	ADAPTED	Inlined, no concurrency
Summary Matrix
API	Category	Adapter	Compiler	VM	RobotAPI	Hardware	Compatibility
GetLightSensorData	HW Primitive	❌	❌	❌	❌	TCRT5000	UNSUPPORTED
GetLightSensor	HW Primitive	✅	✅	✅	✅	Analog	ADAPTED
GetTraceV2I2CState	HW Primitive	❌	❌	❌	❌	TCRT5000	UNSUPPORTED
GetTraceV2I2C	HW Primitive	❌	❌	❌	❌	TCRT5000	UNSUPPORTED
GetTraceV2I2CChxState	HW Primitive	✅	✅	✅	✅	TCRT5000	ADAPTED
SetMoveSpeed	Actuator	❌	❌	❌	❌	Motors	UNSUPPORTED
SetMoveRunSecond	Actuator	✅	✅	✅	✅	Motors	FULL
SetMoveRunAngle	Actuator	❌	❌	❌	❌	Motors+Encoder	UNSUPPORTED
line_set_initialize	Behavior	❌	❌	❌	❌	Motors+Line	UNKNOWN
line_basis	Behavior	❌	❌	❌	❌	Motors+Line	UNKNOWN
line_intersection_stop	Behavior	❌	❌	❌	❌	Motors+Line	UNKNOWN
line_turn_encounterline	Behavior	❌	❌	❌	❌	Motors+Line	UNKNOWN
line_for_bmp	Behavior	❌	❌	❌	❌	Motors+Line	UNKNOWN
_thread.start_new_thread	Runtime	✅	✅	❌	❌	N/A	ADAPTED
Hardware Limitations for RC1
TCRT5000: Only 3 digital channels (L/C/R). No analog, no 8‑eye array.

No encoders: SetMoveRunAngle cannot be implemented accurately.

No analog light sensor: GetLightSensor may not be accurate.

No line following PID: line_* behaviors require a control service.

Next Steps
Define semantics for line_* via reverse‑engineering or user documentation.

Implement missing adapter mappings for GetLightSensorData, GetTraceV2I2CState, GetTraceV2I2C, SetMoveSpeed, SetMoveRunAngle.

Design LineControlService for behavior APIs.

Address threading gap (cooperative scheduler or interpreter).


API	Category	Adapter	Compiler	VM	RobotAPI	Hardware	Overall
SetMoveSpeed	Motion	✅	✅	✅	✅	✅	FULL
Add a note: "Signed independent left/right speeds are preserved. Values are clamped to [-100, 100]."