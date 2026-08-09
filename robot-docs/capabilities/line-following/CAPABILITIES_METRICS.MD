Sprint M5.1.1 – RoboSim Compatibility Matrix (Refined)
Version: 2.0
Status: Architecture Freeze
Owner: DeepSeek
Date: 2026-08-09

1. Purpose
This document is the single source of truth for RoboSim compatibility on the Robot Development Platform.

It defines:

The complete RoboSim API surface (validated against the official specification, not only samples)

Compatibility status per API across seven layers (Frontend, Compiler, VM, RobotAPI, HAL, Physical, Verified)

Semantic classification (Native, Rewrite, NOP, Approximation, Stub, Dummy)

Priority (P0–P3) to guide implementation order

Core vs Full Compatibility metrics to separate essential from optional APIs

API Policy – implementation rules for each semantic class

This document drives all future RoboSim compatibility work (Sprint M5.2+). Every new API implementation must reference this matrix and follow its policies.

2. Core vs Full Compatibility
Core Compatibility (P0–P1)
APIs required for normal RoboSim programming on a typical robot:

Motion (SetMoveRun, SetMoveStop, SetMoveSpeed, SetMoveRunSecond)

Sensor (GetUltrasound, GetTouch, GetLightSensor, GetTraceV2I2CChxState, GetTraceV2I2CData, GetTraceV2I2CState, GetTraceV2I2C)

LED (Set3CLed, SetLightSensorLed)

Audio (SetMp3Play)

Utility (SetWaitForTime)

Language features (loops, conditionals, functions, variables, _thread – though threading is runtime)

These APIs determine whether a standard RoboSim project can execute correctly.

Full Compatibility (P0–P3)
Includes every RoboSim API, regardless of hardware availability:

Servo (SetServo)

Steering (SetSeeringEngine, SetSeeringEngineTime)

Motor (SetMotor, SetMotorServo, SetMotorStraightAngle)

Line behaviors (line_basis, line_millisecond, line_intersection_stop, line_turn_encounterline, line_for_bmp, line_set_initialize)

Peripheral (SetLizard)

GUI-only (UpdateVar, DisplayVariable, etc.)

A robot without a servo should still report 100% Core Compatibility.

3. Expanded API Inventory
All APIs are categorised with their signature, layer support, semantic, and priority.

Legend – Support Layers
Layer	Description
Frontend	RoboSim → Standard Robot API rewriting (AST transformation).
Compiler	AST → bytecode generation; validation.
VM	Bytecode dispatch; opcode handler implemented.
RobotAPI	C++ function exposed to VM; abstraction layer.
HAL	Hardware abstraction (GPIO, PWM, etc.) – driver support.
Physical	Real hardware connected and responds.
Verified	Physical behaviour tested and confirmed.
Status values: ✅, ❌, N/A, PARTIAL (some support).

Semantic Classification
Semantic	Meaning
Native	Implemented exactly as specified; direct hardware control.
Rewrite	Transformed by Frontend into a sequence of native operations.
NOP	No operation at runtime; compile‑only (GUI APIs).
Approximation	Implemented with equivalent behaviour (e.g., time‑based angle).
Stub	RobotAPI exists but does nothing (placeholder).
Dummy	Returns a fixed, deterministic value for queries.
Priority
Priority	Meaning
P0	Critical for Core Compatibility; must be done first.
P1	Important; should be completed in M5.2–M5.3.
P2	Optional but common; schedule for M5.4–M5.5.
P3	Rare or future; may be deferred.
3.1 Motion
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
SetMoveInitialize	(left:int, right:int, reverse:string)	❌	❌	❌	❌	❌	❌	❌	Stub	P1	TODO
SetMoveRun	(direction:string, speed:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
SetMoveRunSecond	(direction:string, speed:int, second:float)	✅	✅	✅	✅	✅	✅	✅	Rewrite	P0	DONE
SetMoveRunAngle	(direction:string, speed:int, angle:int)	❌	❌	❌	❌	❌	❌	❌	Approximation	P1	TODO
SetMoveSpeed	(left_speed:int, right_speed:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
SetMoveStop	()	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
3.2 Sensor
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
GetUltrasound	(port:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
GetTouch	(port:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
GetLightSensor	(port:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
GetLightSensorData	(port:int)	❌	❌	❌	❌	❌	❌	❌	Dummy	P2	TODO
GetTraceV2I2CState	(port:int, channel:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
GetTraceV2I2C	(port:int, channel:int)	✅	✅	✅	✅	✅	✅	✅	Dummy	P1	DONE
GetTraceV2I2CData	(port:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
GetTraceV2I2CChxState	(port:int, channel:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
3.3 LED & Audio
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
Set3CLed	(port:int, state:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
SetLightSensorLed	(port:int, state:int)	✅	✅	✅	✅	✅	✅	✅	Native	P0	DONE
SetMp3Play	(index:int)	✅	✅	✅	✅	✅	✅	✅	Approximation	P0	DONE
3.4 Servo & Steering
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
SetServo	(port:int, angle:int)	✅	✅	✅	✅	❌	❌	❌	Stub	P2	PARTIAL
SetSeeringEngine	(port:int, angle:int)	❌	❌	❌	❌	❌	❌	❌	Stub	P2	TODO
SetSeeringEngineTime	(port:int, angle:int, millisecond:int)	❌	❌	❌	❌	❌	❌	❌	Stub	P2	TODO
3.5 Motor (DC)
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
SetMotor	(port:int, speed:int)	❌	❌	❌	❌	❌	❌	❌	Native	P2	TODO
SetMotorServo	(port:int, speed:int, angle:int)	❌	❌	❌	❌	❌	❌	❌	Native	P2	TODO
SetMotorStraightAngle	(left_port:int, right_port:int, speed:int, angle:int)	✅	✅	✅	✅	❌	❌	❌	Stub	P1	PARTIAL
3.6 Line Following (Behaviors)
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
line_set_initialize	(port:int, color:string, chassisType:string)	❌	❌	❌	❌	❌	❌	❌	Stub	P2	TODO
line_basis	(speed:int)	✅	✅	✅	✅	✅	✅	❌	Native	P1	DONE (needs verification)
line_millisecond	(speed:int, millisecond:int)	❌	❌	❌	❌	❌	❌	❌	Approximation	P1	TODO
line_intersection_stop	(speed:int, type:int)	✅	✅	✅	✅	❌	❌	❌	Stub	P1	PARTIAL
line_turn_encounterline	(speed:int, angle:int, direction:int)	❌	❌	❌	❌	❌	❌	❌	Native	P1	TODO
line_for_bmp	(speed:int, degree:int)	❌	❌	❌	❌	❌	❌	❌	Approximation	P2	TODO
3.7 Peripheral
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
SetLizard	(state:int)	❌	❌	❌	❌	❌	❌	❌	Stub	P3	TODO
3.8 Utility
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
SetWaitForTime	(second:float)	✅	✅	✅	✅	✅	✅	✅	Rewrite	P0	DONE
3.9 GUI‑Only (not in samples but present in spec)
API	Signature	Frontend	Compiler	VM	RobotAPI	HAL	Physical	Verified	Semantic	Priority	Status
UpdateVar	(name:string, value:any)	✅	✅	✅ (NOP)	N/A	N/A	N/A	N/A	NOP	P3	DONE (NOP)
DisplayVariable	(name:string)	✅	✅	✅ (NOP)	N/A	N/A	N/A	N/A	NOP	P3	DONE (NOP)
3.10 Runtime / Language
Feature	Frontend	Compiler	VM	Status	Semantic	Priority
while True / while 1	N/A	✅	✅	DONE	Native	P0
if / else	N/A	✅	✅	DONE	Native	P0
for i in range()	N/A	✅	✅	DONE	Native	P0
break / continue	N/A	✅	✅	DONE	Native	P0
Global variables	N/A	✅	✅	DONE	Native	P0
User-defined functions	N/A	✅	✅	DONE	Native	P0
_thread.start_new_thread	✅	✅	❌	PARTIAL	Rewrite	P1
4. Compatibility Metrics
Core Compatibility (P0–P1 APIs)
Core APIs are those marked P0 or P1 that are essential for basic robot programming.
Total Core APIs: 20 (Motion 5 + Sensor 6 + LED/Audio 3 + Utility 1 + Language features 5).
Supported (Frontend→Compiler→VM→RobotAPI→HAL→Physical→Verified): 14 (those with ✅ in all seven layers).

Core compatibility: 14 / 20 = 70%.

Full Compatibility (All APIs)
Total inventoried APIs (excluding language features): 31.
Fully supported (all seven layers): 14 (same list).
Partial support (some layers): 3 (SetServo, SetMotorStraightAngle, line_intersection_stop).
TODO: 14 (including SetMoveInitialize, SetMoveRunAngle, SetLightSensorData, SetSeeringEngine, SetMotor, line_*, SetLizard, etc.).

Full compatibility (DONE only): 14 / 31 = 45.2%.
Full compatibility (DONE + PARTIAL): 17 / 31 = 54.8%.

5. API Policy
This section defines the implementation policy for each semantic classification. All API implementations must follow these rules.

5.1 Native
Implemented exactly as specified.

Direct hardware control (or direct sensor read).

No transformation at Frontend.

Must be supported across all layers.

Example: SetMoveRun, GetUltrasound.

5.2 Rewrite
Transformed by Frontend into a sequence of native operations.

The rewritten code uses only native APIs.

The compiler never sees the original RoboSim call.

Example: SetMoveRunSecond → forward + wait + stop.

5.3 NOP
Compile succeeds; runtime does nothing.

Used for GUI-only APIs or platform‑specific stubs.

No RobotAPI or HAL required.

Example: UpdateVar, DisplayVariable.

5.4 Approximation
Implemented using equivalent behaviour when exact semantics are impossible.

Must be clearly documented as an approximation.

Example: SetMoveRunAngle – if no encoder, use time‑based estimation.

5.5 Stub
RobotAPI function exists but performs no action (or logs).

Used when hardware is not available, but the call must not crash.

Example: SetServo on a robot without servo.

5.6 Dummy
Query API returns a fixed, deterministic value.

Useful for sensors not physically present.

Must log clearly as dummy.

Example: GetLightSensorData (if no digital light sensor).

5.7 General Rules
Compiler must accept every API – no “unknown function” errors.

Physical availability must not affect compiler success – compile always PASS.

Hardware‑specific APIs must never leak into RoboSim – only platform HAL/SDK.

All blocking APIs must be thread‑local when threading is implemented.