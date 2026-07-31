# RoboSim RC1 API Contract

**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Draft for Review  

---

## Purpose

This document defines the **official contract** for the set of RoboSim APIs required to run the RC1 acceptance program on the Robot Platform v1 hardware.

---

## Scope

Only APIs appearing in the RC1 acceptance program are covered.

---

## API Definitions

### 1. Light Sensor (Digital) — `GetLightSensorData(port)`

**Signature:**
```python
int GetLightSensorData(int port)
Semantics:
Returns digital state (0 or 1) from a light sensor connected to port. Typically used with TCRT5000 as a simple light/dark detector.

Parameters:

port: integer (1‑based or 0‑based, depends on RoboSim). Usually 1.

Return:
0 = no light / dark?
1 = light detected? (Need confirmation)

Mapping to Robot Platform:

Hardware: TCRT5000 digital output.

We will map to read_line(channel) if port corresponds to one of L/C/R, or to a dedicated light sensor pin.

Contract:

Adapter must transform to Standard Robot API read_light_digital(port).

Compiler must support opcode ReadLightDigital.

VM must handle it.

RobotAPI must provide ReadLightDigital(int port).

Blocking: No.

2. Light Sensor (Analog) — GetLightSensor(port)
Signature:

python
int GetLightSensor(int port)
Semantics:
Returns analog value (0‑1023 or 0‑4095) from a light sensor.

Mapping:
Already supported via read_light(port) → ReadLight opcode.

Contract:

Maintain current implementation.

If analog hardware unavailable, document limitation.

Blocking: No.

3. Trace Sensor State — GetTraceV2I2CState(port, channel)
Signature:

python
int GetTraceV2I2CState(int port, int channel)
Semantics:
Unknown. Likely returns boolean state of a specific channel in a multi‑eye trace array.

Mapping to Robot Platform:
We will treat it as read_line(channel) (digital) for channel 0..2.

Contract:

Adapter maps to read_line(channel) using the second argument as channel.

Compiler/VM/RobotAPI reuse existing ReadLine.

Blocking: No.

4. Trace Sensor Raw — GetTraceV2I2C(port, channel)
Signature:

python
int GetTraceV2I2C(int port, int channel)
Semantics:
Unknown. Might return raw sensor value (analog) or position.

Platform Decision:
With TCRT5000 digital only, this API will be UNSUPPORTED for RC1. The program uses GetTraceV2I2C(1, 1) == 50, suggesting it expects a numeric range. We cannot support this without analog or 8‑eye array.

Contract:

Mark as UNSUPPORTED in RC1.

If the program fails, we may need to adjust the program or emulate via digital.

5. Trace Channel State — GetTraceV2I2CChxState(port, channel)
Signature:

python
int GetTraceV2I2CChxState(int port, int channel)
Semantics:
Returns digital state (0/1) of a specific channel in a trace sensor array.

Mapping:
Already supported via read_line(channel).

Contract:

Adapter maps to read_line(channel) where channel = second argument (0,1,2 for L/C/R).

Port is ignored.

Blocking: No.

6. Direct Motor Speed — SetMoveSpeed(left, right)
Signature:

python
void SetMoveSpeed(int left, int right)
Semantics:
Set left and right motor speeds directly. Values typically -100..100.

Mapping:
Need new opcode SetMotorSpeed and RobotAPI SetMotorSpeed(int left, int right). It will call setMotorsDirect() internally.

Contract:

Adapter maps SetMoveSpeed(l, r) to set_motor_speed(l, r).

Compiler generates SetMotorSpeed opcode with two operands.

VM handler calls RobotAPI::SetMotorSpeed(left, right).

RobotAPI uses HAL PWM.

Blocking: No.

7. Timed Move — SetMoveRunSecond(direction, speed, seconds)
Signature:

python
void SetMoveRunSecond(string direction, int speed, float seconds)
Semantics:
Move in direction at speed for seconds seconds, then stop. Blocking.

Mapping:
Already supported.

Contract:

Keep existing adapter that expands to forward(speed); wait(seconds*1000); stop().

Compiler, VM, RobotAPI unchanged.

Blocking: Yes.

8. Angle Move — SetMoveRunAngle(direction, speed, angle)
Signature:

python
void SetMoveRunAngle(string direction, int speed, int angle)
Semantics:
Move in direction at speed for angle degrees (based on encoders or timing). Blocking.

Mapping:
Not supported (no encoders). We may approximate by timing if angle → duration mapping is known.

Contract:

For RC1, we will implement a timing‑based approximation:

Convert angle to duration using a calibration constant (e.g., 1 sec = 90°).

Use SetMoveRunSecond internally.

Document that accuracy is limited.

Blocking: Yes.

9. Line Behavior — line_basis(speed)
Signature:

python
void line_basis(int speed)
Semantics:
Unknown. Likely starts basic line following (PID‑less) at given speed.

Platform Decision:
We need to define a simple line‑following behavior:

Read all 3 line sensors.

If center black → forward.

If left black → turn left.

If right black → turn right.

Stop when all white (optional).

Contract:

Adapter maps to line_follow(speed).

Compiler generates LineFollow opcode (behavior).

VM calls RobotAPI::LineFollow(speed).

RobotAPI implements the logic using SensorManager and motors.

Behavior is blocking (runs until line lost or timeout).

Blocking: Yes.

10. Line Intersection Stop — line_intersection_stop(speed, type)
Signature:

python
void line_intersection_stop(int speed, int type)
Semantics:
Unknown. Likely follows line until an intersection of type is detected, then stops.

Platform Decision:

Detect intersection when all 3 sensors are black (or a pattern).

Stop motors.

Contract:

Adapter maps to line_follow_until_intersection(speed, type).

Compiler/VM/RobotAPI similar to line_basis.

Blocking.

Blocking: Yes.

11. Line Turn Until Line — line_turn_encounterline(speed, angle, direction)
Signature:

python
void line_turn_encounterline(int speed, int angle, int direction)
Semantics:
Unknown. Likely turns until a line is detected.

Platform Decision:

Turn in given direction until center line sensor detects black, then stop.

Angle may be a timeout or max turn angle.

Contract:

Adapter maps to line_turn_until_line(speed, angle, direction).

Blocking.

Blocking: Yes.

12. Line Bitmap — line_for_bmp(speed, degree)
Signature:

python
void line_for_bmp(int speed, int degree)
Semantics:
Unknown. Possibly follows a black line for a specified degree/path.

Platform Decision:

Unclear. We will defer implementation until semantics are clarified.

Contract:

Mark as UNSUPPORTED for RC1. If the program uses it, we may need to stub or remove.

13. Line Initialize — line_set_initialize(port, color, chassisType)
Signature:

python
void line_set_initialize(int port, string color, string chassisType)
Semantics:
Unknown. Likely configures line sensor parameters.

Platform Decision:

We will ignore this call (no‑op) because our hardware is fixed (3‑eye TCRT5000, black line).

Contract:

Adapter maps to line_initialize(port, color, chassisType) but does nothing.

Compiler may emit LineInit opcode that does nothing.

Blocking: No.

14. Thread Start — _thread.start_new_thread(func, ())
Signature:

python
void _thread.start_new_thread(function, tuple)
Semantics:
Spawns a new thread.

Platform Decision:

Currently inlined (no concurrency).

For RC1, we will implement a cooperative scheduler in the VM:

Each _thread.start_new_thread registers a function.

The VM executes one instruction from each thread in round‑robin.

Wait (blocking) will yield to other threads.

Contract:

Adapter: keep current transformation to function call.

Compiler: instead of inlining, emit ThreadStart opcode.

VM: manage multiple contexts.

Blocking: No.

Summary of Contract Changes Needed
API	Action
GetLightSensorData	Add adapter mapping, compiler opcode, VM handler
GetLightSensor	Already supported
GetTraceV2I2CState	Add adapter mapping to read_line
GetTraceV2I2C	UNSUPPORTED for RC1
GetTraceV2I2CChxState	Already supported
SetMoveSpeed	Add opcode and RobotAPI
SetMoveRunSecond	Already supported
SetMoveRunAngle	Implement timing‑based approximation
line_basis	Implement simple line following behavior
line_intersection_stop	Implement intersection detection and stop
line_turn_encounterline	Implement turn‑until‑line behavior
line_for_bmp	UNSUPPORTED (defer)
line_set_initialize	No‑op
_thread.start_new_thread	Implement cooperative scheduler
Hardware Assumptions
3‑eye TCRT5000 line sensors on L/C/R pins.

No encoders.

No analog line sensor.

2 DC motors with PWM control.

RC1 Success Criteria
The RC1 program must:

Compile without errors.

Execute on the VM (either with or without threading).

Produce observable motor behavior based on sensor inputs.

Some APIs may be stubbed or approximated, but the robot must not crash.

## Time Units

- `SetWaitForTime(seconds)` – The argument is in **seconds**. The frontend converts it to milliseconds.
- `SetMoveRunSecond(direction, speed, seconds)` – The duration is in **seconds**, converted to milliseconds.
- Canonical `wait(milliseconds)` – Always in **milliseconds**.
- VM/Firmware `Wait` – **milliseconds** (uint32_t).
- Conversion happens exclusively in the frontend adapter; no other layer performs unit conversion.