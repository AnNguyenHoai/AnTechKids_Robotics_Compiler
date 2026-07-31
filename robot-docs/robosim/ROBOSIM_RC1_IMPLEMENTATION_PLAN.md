## Sprint S3.1 — Adapter & Compiler Extensions

**Goal:** Extend `robot-frontend-robosim` and `robot-compiler` to support missing hardware primitives.

### Tasks

#### 1. Add `GetLightSensorData` mapping
- File: `frontend/mapping.py`
- Add entry:
```python
"GetLightSensorData": {
    "target": "read_light_digital",
    "arg_indices": [0],
    "expected_args": 1,
}
Create compiler handler for read_light_digital in SensorHandler.

New opcode: ReadLightDigital.

2. Add GetTraceV2I2CState mapping
Mapping to read_line(channel) (use second arg).

No new opcode needed; reuse ReadLine.

3. Add SetMoveSpeed mapping
Adapter maps to set_motor_speed(left, right).

Compiler: new opcode SetMotorSpeed with two operands.

VM handler: call RobotAPI::SetMotorSpeed(left, right).

RobotAPI: add void SetMotorSpeed(int left, int right) using HAL.

4. Add SetMoveRunAngle timing‑based implementation
Adapter: transform to set_move_run_time(direction, speed, angle * calibration)

Where calibration = seconds per degree (e.g., 1 sec = 90° → 0.0111 sec/deg).

Use existing SetMoveRunSecond adapter.

Deliverables
Updated mapping.py

New opcode SetMotorSpeed in api.yaml

Updated function_registry.py and opcode.h (rebuild)

Updated RobotAPI.cpp with SetMotorSpeed

Sprint S3.2 — Line Behavior Service
Goal: Implement line_* APIs as high‑level behaviors using SensorManager and Motor control.

Architecture
Create LineControlService (or integrate into RobotAPI).

Behaviors are blocking and use polling loops.

Tasks
1. line_basis(speed)
Simple line follower:

Read L/C/R.

If center black: forward.

If left black: turn left.

If right black: turn right.

Else: stop (or search).

Runs until stop() called or timeout.

2. line_intersection_stop(speed, type)
Follow line until intersection detected (all 3 black).

Then stop.

type parameter ignored.

3. line_turn_encounterline(speed, angle, direction)
Turn in given direction until center line sensor detects black.

If angle exceeded, stop.

Use SetMoveSpeed with opposite speeds.

4. line_set_initialize(port, color, chassisType)
No‑op.

5. line_for_bmp(speed, degree)
Defer to future; for RC1, implement as no‑op or simple loop.

Deliverables
LineControlService.h/.cpp in robot-platform/main/src/Services/Line/

Updated RobotAPI with LineFollow, LineIntersectionStop, etc.

Compiler opcodes for each behavior (or use Call to a runtime function).

Sprint S3.3 — Cooperative Scheduler (VM Threading)
Goal: Enable concurrent execution of multiple tasks.

Tasks
1. Refactor VM to support multiple threads
Define ThreadContext struct.

VM holds array of MAX_THREADS contexts.

currentThread index.

LoadProgram initializes main thread.

2. Implement ThreadStart opcode
Compiler: emit ThreadStart for _thread.start_new_thread.

VM: on ThreadStart, create new thread context at function entry.

3. Implement round‑robin scheduling
In Step(), after executing one instruction, move to next READY thread.

If current thread is BLOCKED and wakeup time reached, make it READY.

4. Make Wait yielding
Wait handler sets thread state to BLOCKED and wakeup time.

Does not call delay().

5. Update compiler to not inline _thread.start_new_thread
Remove inlining in RoboSimTransformer.

Keep _thread.start_new_thread as a recognizable function call.

Compiler handles _thread.start_new_thread differently.

Deliverables
Updated VM.h, VM.cpp

Updated Compiler to emit ThreadStart.

Updated RobotAPI::Wait to use thread‑local blocking (or keep as is if VM handles it).

Sprint S3.4 — Validation & Integration
Goal: Run RC1 program end‑to‑end and fix bugs.

Tasks
1. Create RC1 test program
Place rc1_program.py in examples/robosim/.

Verify compilation.

2. Run on VM (mock hardware)
Observe motor commands and sensor reads.

Debug threading and behavior.

3. Run on physical robot (ESP32)
Flash firmware.

Verify actual behavior.

4. Fix issues
Tune line following parameters.

Adjust timing for SetMoveRunAngle.

Handle sensor noise.

Deliverables
Passing test report.

Updated calibration constants.

Sprint S3.5 — Documentation & Release
Goal: Finalize RC1 documentation.

Tasks
1. Update user documentation
ROBOSIM_RC1_COMPATIBILITY.md

Supported API list.

2. Update architecture docs
Threading model.

Line behavior service.

3. Tag release
RC1 tag in repository.

Timeline Estimate
Sprint	Duration	Effort
S3.1	2 days	2 devs
S3.2	3 days	1 dev
S3.3	3 days	1 dev
S3.4	2 days	1 dev
S3.5	1 day	1 dev
Total	11 days	
Risks
Risk	Mitigation
line_* semantics unknown	Reverse‑engineer or define reasonable behavior
Threading bugs	Extensive testing on mock hardware
Physical robot behavior not matching	Calibration and tuning
Performance (VM too slow)	Optimize later; RC1 is prototype