# AnTechKids Robotics V2 — Software Development Requirements

**Project:** AnTechKids Robotics Platform  
**Revision:** V2.0-dev  
**Document type:** Software Requirements / Development Backlog / Development Source of Truth  
**Status:** ACTIVE — authoritative source of truth for V2 implementation  
**V2 development branch:** `main_V2`  
**V1 frozen baseline:** `main@eb1b6f506be4155cfcf8ebb563d82ba92ad789d6`  
**Phase 0 status:** COMPLETE — requirements reconciled against frozen V1 baseline  
**Related hardware baselines:**  
- `Connector_Electrical_Interface_v2_FREEZE.md`
- `Power_BMS_V2_and_Complete_BOM.md`

---

# 1. Purpose

Tài liệu này gom toàn bộ software requirements cần phát triển để đưa robot từ hardware/software V1 hiện tại lên kiến trúc V2 đã được freeze.

Mục tiêu chính:

1. Giữ lại compiler, VM, hardware feature framework, encoder implementation, network/OTA foundation và RoboStudio capability validation hiện có.
2. Tách rõ **BoardProfile = physical truth** và **HardwareConfig = feature enable/disable**.
3. Bổ sung Motor hardware safe-state + START/ARM.
4. Chuẩn hóa shared System I2C bus.
5. Tích hợp MCP23017 cho Line5, LEDs và buzzer.
6. Migrate Line5 physical acquisition từ direct GPIO sang MCP23017 trong khi giữ nguyên public 5-channel semantics.
7. Hoàn thiện Servo từ DUMMY thành real hardware output.
8. Bổ sung battery/reset/system health.
9. Expose Robot Health qua HTTP, OLED và RoboStudio.
10. Giữ backward compatibility ở mức hợp lý với software hiện tại.

## 1.1 Source-of-truth governance

Tài liệu này là **source of truth bắt buộc** cho toàn bộ development V2 trên branch `main_V2`.

Quy tắc phát triển:

1. Mọi task V2 phải trace được về ít nhất một requirement ID trong tài liệu này.
2. Trước khi đóng một task, developer phải cập nhật requirement liên quan trong chính file này:
   - trạng thái;
   - implementation note nếu architecture/behavior đã được chốt;
   - test/verification status;
   - deviation hoặc decision mới nếu có.
3. Không được coi task là `DONE` nếu code đã merge nhưng source-of-truth chưa được cập nhật.
4. Nếu implementation phát hiện requirement sai, conflict hoặc không còn phù hợp:
   - không silently diverge;
   - phải sửa requirement;
   - ghi decision/deviation;
   - sau đó mới tiếp tục implementation.
5. `main_V2` là nhánh phát triển V2 chính. V1 frozen baseline dùng để đối chiếu compatibility là:
   `main@eb1b6f506be4155cfcf8ebb563d82ba92ad789d6`.
6. Hardware-only acceptance criteria chưa thể verify khi chưa có hardware phải được ghi rõ `PENDING_HW`, không được đánh dấu PASS giả.
7. Status chuẩn dùng trong tài liệu:
   - `PLANNED`
   - `IN_PROGRESS`
   - `IMPLEMENTED`
   - `VERIFIED_SW`
   - `PENDING_HW`
   - `DONE`
   - `BLOCKED`

## 1.2 Requirement change discipline

Mọi thay đổi requirement sau Phase 0 phải giữ được traceability. Tối thiểu cần trả lời:

```text
What changed?
Why?
Which requirement/task is affected?
Backward compatibility impact?
Software verification available?
Hardware verification pending?
```

Requirement source-of-truth được phép tiến hóa trong quá trình V2 development, nhưng mọi thay đổi phải được check-in cùng branch `main_V2`.

---

# 2. Existing software baseline

Các thành phần hiện tại được xem là foundation và **không rewrite nếu không có lý do kỹ thuật rõ ràng**:

- Python/RoboSim frontend
- Robot compiler
- VM / bytecode runtime
- Robot public API surface
- Hardware feature registry
- `hardware.json`
- `generated_device_config.h`
- `ROBOT_FEATURE_*`
- Hardware Requirement Validator
- Hardware ON/OFF Build Matrix
- Encoder implementation
- Motor motion/heading implementation
- Robot Network Service
- OTA infrastructure
- Robot Identity / capability advertisement
- Existing diagnostics framework

Các gap chính của V1 cần xử lý:

- static GPIO mapping;
- no BoardProfile abstraction;
- no MCP23017;
- no shared I2C ownership;
- direct-GPIO Line5 acquisition must migrate behind MCP23017 while preserving the V1 Line5 logical contract;
- Servo firmware still DUMMY;
- LED/Buzzer direct GPIO assumptions;
- no Motor ARM/STBY runtime safety state;
- VM may execute immediately after boot;
- `/api/v1/health` only exposes basic ready/network/OTA state;
- no battery health;
- no reset reason;
- no OLED health display;
- no RoboStudio Robot Health panel.

---

# 3. Phase 0 — Requirements Reconciliation & V1 → V2 Delta

## Status

**COMPLETE**

Phase 0 được thực hiện trước khi bắt đầu V2 implementation để reconcile requirements với V1 frozen baseline.

Frozen baseline:

```text
branch: main
commit: eb1b6f506be4155cfcf8ebb563d82ba92ad789d6
```

V2 development branch:

```text
main_V2
```

## 3.1 Compatibility decisions frozen in Phase 0

### Decision P0-D01 — Public Line channel IDs remain backward compatible

V1 Line5 đã freeze public channel semantics:

```text
0 = Left
1 = Center
2 = Right
3 = Far Left
4 = Far Right
```

V2 shall preserve this public mapping.

The physical MCP23017 Port-A bit order is an implementation detail and shall not redefine public API channel IDs.

Rationale:

- legacy 3-channel student programs depend on `0=Left, 1=Center, 2=Right`;
- V2 requirement explicitly requires existing 3-channel programs to remain functionally valid;
- renumbering channels would create an avoidable public API breaking change.

### Decision P0-D02 — Canonical Line5 raw mask remains backward compatible

V1 Line5 canonical software mask is frozen as:

```text
bit4 bit3 bit2 bit1 bit0
 FL    L    C    R    FR
```

Equivalent constants:

```text
Far Left  = 0x10
Left      = 0x08
Center    = 0x04
Right     = 0x02
Far Right = 0x01
MASK_ALL  = 0x1F
```

V2 `LineSensorBank` shall convert MCP23017 Port-A physical inputs into this canonical mask.

The physical MCP bit allocation must not leak through `GetTraceRaw()`.

### Decision P0-D03 — Reuse V1 Line5 perception/control

The following V1 Line5 logic is considered a reusable software foundation and shall not be rewritten merely because V2 moves sensing behind MCP23017:

```text
LineSensorLayout
LineErrorEstimator
LinePerception
IntersectionDetector
RecoveryStrategy
FollowerStateMachine
LineFollower
line diagnostics
public Line APIs
```

V2 shall replace the physical acquisition path while preserving the canonical logical mask contract.

Any algorithm changes after hardware validation shall be treated as explicit requirement changes/tuning tasks.

### Decision P0-D04 — BoardProfile and HardwareConfig have separate ownership

```text
BoardProfile
    = physical truth / fixed V2 wiring

HardwareConfig
    = capability enable/disable state
```

Feature ON/OFF must never remap a V2 physical connector.

### Decision P0-D05 — MotorSafety is independent of VM/student behavior

VM execution and public motion API calls may exist while SAFE, but physical motor output permission is owned only by `MotorSafetyController`.

No student program, VM opcode, behavior layer or public RobotAPI path may bypass the lowest common physical motor safety gate.

## 3.2 V1 → V2 delta matrix

| Area | V1 frozen baseline | V2 target | Required action | Phase-0 disposition |
|---|---|---|---|---|
| Compiler/frontend | Existing and working | Preserve | REUSE | Frozen |
| VM / bytecode runtime | Existing and working | Preserve | REUSE | Frozen |
| Public Robot API | Existing | Preserve compatibility | REUSE/ADAPT | Frozen |
| Hardware feature framework | `hardware.json`, generated config, `ROBOT_FEATURE_*` | Preserve | REUSE | Frozen |
| Board wiring source | Static/scattered GPIO aliases | `BoardProfile` | NEW/MIGRATE | Planned |
| System I2C | No single owner | Shared bus manager | NEW/REFACTOR | Planned |
| MCP23017 | None | HAL at `0x20` | NEW | Planned |
| Line physical acquisition | 5 direct ESP32 GPIO inputs | MCP23017 Port A bank | MIGRATE | Planned |
| Line public channels | `0=L,1=C,2=R,3=FL,4=FR` | Same | REUSE | **Frozen** |
| Line canonical raw mask | `bit4..0 = FL,L,C,R,FR` | Same | REUSE + physical conversion | **Frozen** |
| Line estimator/perception | 5CH weighted baseline | Preserve | REUSE/TUNE after HW | Frozen |
| Intersection/recovery | 5CH software baseline | Preserve then HW-tune | REUSE/TUNE | Frozen |
| Encoder implementation | Existing | Preserve | REUSE + V2 mapping | Planned |
| Motor motion/heading | Existing | Preserve | REUSE under safety gate | Planned |
| Motor hardware enable | No centralized STBY ownership | GPIO4 MotorSafety gate | NEW | Planned |
| START/ARM | None | GPIO33 active-low | NEW | Planned |
| Servo | DUMMY | Real GPIO16/17 PWM | IMPLEMENT | Planned |
| LED/Buzzer | Direct GPIO assumptions | MCP23017 Port B | MIGRATE | Planned |
| Battery | None | GPIO32 ADC monitor | NEW | Planned |
| Reset reason | None | normalized reset service | NEW | Planned |
| Health | Basic network/OTA readiness | RobotHealth source of truth | EXTEND | Planned |
| OLED | None | Optional health display | NEW | Planned |
| RoboStudio | Capability config | Board-aware + health | EXTEND | Planned |

## 3.3 Phase 0 exit criteria

Phase 0 is complete because:

- V2 development baseline commit is explicit and immutable for comparison.
- `main_V2` is the dedicated V2 branch.
- public Line channel compatibility conflict has been resolved.
- raw-mask ordering conflict has been resolved.
- V1 Line5 reusable logic has been identified.
- BoardProfile/HardwareConfig ownership is frozen.
- MotorSafety ownership boundary is frozen.
- source-of-truth update discipline is defined.

---

# 4. Priority definition

| Priority | Meaning |
|---|---|
| P0 | Safety/platform blocker. Must complete before V2 robot is allowed to operate normally. |
| P1 | Required V2 functionality. Must complete before V2 feature-complete release. |
| P2 | UX/diagnostic enhancement. Can follow after core V2 is stable. |

---

# 5. Milestone overview

| Milestone | Name | Primary goal |
|---|---|---|
| M0 | Requirements Reconciliation | Freeze compatibility, ownership boundaries and V1→V2 delta |
| M1 | V2 Platform Foundation | BoardProfile + shared I2C + MCP23017 foundation |
| M2 | Motor Safety & ARM | Hardware-gated motor safety independent from student code |
| M3 | V2 Hardware Features | Line5 + Servo + LED/Buzzer migration |
| M4 | Robot Health Platform | Battery, reset reason, health aggregate, API, OLED |
| M5 | RoboStudio V2 Integration | Board awareness, config migration, Robot Health panel |
| M6 | Verification & Release Hardening | Regression, latency, safety, compatibility, release readiness |

Recommended implementation order:

```text
M0 Requirements Reconciliation
        |
        v
M1 Platform Foundation
        |
        v
M2 Motor Safety
        |
        v
M3 Hardware Features
        |
        v
M4 Robot Health
        |
        v
M5 RoboStudio
        |
        v
M6 Verification / Release
```

---

# 6. Milestone M1 — V2 Platform Foundation

## Goal

Tạo physical board abstraction ổn định trước khi migrate peripheral.

---

## V2-SW-001 — Board Profile Contract

**Priority:** P0  
**Status:** DONE

### Requirement

Software shall separate:

```text
BoardProfile
    = fixed physical wiring

HardwareConfig
    = enabled/disabled feature state
```

V2 board shall be identified by a stable board profile, for example:

```text
antech_robot_v2
```

BoardProfile shall own at minimum:

```text
GPIO4  MOTOR_SAFE_EN

GPIO13 SYSTEM_I2C_SCL
GPIO21 SYSTEM_I2C_SDA

GPIO14 MOTOR_R
GPIO25 MOTOR_L
GPIO26 MOTOR_L
GPIO27 MOTOR_R

GPIO16 SERVO1
GPIO17 SERVO2

GPIO22 ULTRASONIC_ECHO
GPIO23 ULTRASONIC_TRIG

GPIO32 BATTERY_ADC
GPIO33 START_ARM

GPIO34 ENCODER_L_A
GPIO35 ENCODER_L_B
GPIO36 ENCODER_R_A
GPIO39 ENCODER_R_B

MCP23017 address 0x20
```

HardwareConfig shall not be allowed to remap connector GPIO ownership.

### Acceptance criteria

- Changing `line_sensor`, `encoder`, `servo`, etc. ON/OFF does not change board wiring.
- One physical connector always maps to the same signals.
- Board mapping is centralized and testable.
- Existing code paths no longer depend on scattered V1 GPIO constants where V2 BoardProfile should be authoritative.

### Implementation / verification record

**Implementation commits:** `23c53d2ef06e559de2648d4680392052f897aaaf` (contract + test) and `68b01d9447fa812993a6b0a9a23f90dca12fc6cd` (focused CI gate)

Implemented contract:

- `robot-platform/main/src/HardwareAbstraction/BoardProfile.h` is the authoritative V2 physical mapping.
- Stable profile ID: `antech_robot_v2`.
- `GPIO.h` is retained only as a compatibility facade for existing firmware call sites and delegates V2-owned signals to `BoardProfile`.
- Existing V1 Line5 direct-GPIO aliases are explicitly transitional debt and must be removed by `V2-SW-004`; they are not part of V2 physical truth.
- Existing LED/Buzzer direct-GPIO aliases are explicitly transitional debt for `V2-SW-008`.
- `robostudio/config/hardware.json` and `generated_device_config.h` remain feature enable/disable sources only and do not own connector/pin mapping.
- `tests/v2_board_profile/run_v2_board_profile.py` locks the fixed mapping and ownership boundary.
- The BoardProfile contract test is registered in `run_all_tests.py`.

Software verification:

- Board mapping contract: covered by `tests/v2_board_profile/run_v2_board_profile.py`.
- HardwareConfig cannot remap wiring: covered by the same regression.
- Focused contract verification passed: fixed mapping, GPIO facade delegation, and HardwareConfig ownership assertions.
- `BoardProfile.h` passed a C++11 compile/static-assert smoke check.
- No hardware is required to verify this ownership/mapping contract.
- Hardware-dependent electrical validation belongs to later peripheral tasks and remains outside V2-SW-001.
- Dedicated GitHub Actions gate `.github/workflows/v2-board-profile-contract.yml` is active on `main_V2`.
- GitHub Actions run `37405436764` completed successfully against commit `6eae9ebdfe415c67423530ab785814499577c789`.

**Verification status:** `VERIFIED_SW`  
**Task status:** `DONE`

### Dependencies

None.

---

## V2-SW-002 — System I2C Bus Manager

**Priority:** P0  
**Status:** PENDING_HW

### Requirement

One software owner shall initialize and manage:

```text
SDA = GPIO21
SCL = GPIO13
Initial frequency = 400 kHz
Logic = 3.3 V
```

Expected bus devices:

```text
MCP23017
OLED
MPU6050
Current monitor
Future health devices
```

Peripheral drivers shall not independently call `Wire.begin(...)`.

### Acceptance criteria

- System I2C initializes exactly once.
- MPU6050 continues to work through shared bus.
- MCP23017 can coexist with MPU6050.
- Bus initialization is deterministic after reset.
- Device failure does not permanently block main loop.

### Implementation / verification record

**Implementation commits:** `780ac7ec703deafd6fdc02ee851a6507e1657c30` (shared bus manager + MPU migration + tests/CI), `2fe0eb8bdd7e385a9597985d94a7fe85cfbc0958` and `0dccf474a3c44e42fcee5da5272b35edace3b009` (ownership-regression false-positive hardening).

Implemented contract:

- `SystemI2CBusManager` is the single software owner of `Wire.begin(...)`.
- Physical bus configuration is sourced only from `BoardProfile`: SDA GPIO21, SCL GPIO13, initial 400 kHz.
- Bus initialization is attempted at most once per boot and is idempotent for all later consumers.
- A finite 20 ms Wire transaction timeout is configured so a missing/misbehaving I2C device cannot create an unbounded wait at the shared-bus layer.
- `RobotAPI::Initialize()` initializes System I2C before `SensorManager::initializeAll()`, independent of optional IMU/device feature flags.
- MPU6050 no longer calls `Wire.begin(...)`; it consumes the shared bus through `ensureInitialized()`.
- Shared-bus initialization failure is diagnostic and non-blocking; boot continues and individual I2C peripherals may report unavailable.
- Contract regression is implemented at `tests/v2_system_i2c/run_v2_system_i2c.py` and registered in `run_all_tests.py`.
- Dedicated CI gate: `.github/workflows/v2-system-i2c-contract.yml`.

Software verification covers:

- fixed SDA/SCL/frequency contract;
- exactly one `Wire.begin(...)` owner in robot-platform;
- idempotent one-attempt initialization;
- finite I2C timeout/no retry loop;
- platform init ordering before sensors;
- MPU6050 shared-bus migration.
- Focused GitHub Actions `V2 System I2C Contract` run `37406127227`: **PASS** on `0dccf474a3c44e42fcee5da5272b35edace3b009`.

Hardware-dependent acceptance criteria:

- MPU6050 communication on physical V2 bus: `PENDING_HW`.
- MCP23017 + MPU6050 coexistence: `PENDING_HW` (also depends on V2-SW-003).
- reset-level deterministic physical bus behavior: `PENDING_HW`.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SW-001.

---

## V2-SW-003 — MCP23017 Driver/HAL

**Priority:** P0  
**Status:** PENDING_HW

### Requirement

Implement a dedicated MCP23017 driver.

Minimum capabilities:

```cpp
begin()
configureInput()
configureOutput()
readPortA()
readPortB()
readPin()
writePin()
healthy()
```

Required addressing:

```text
I2C address = 0x20
```

Initial allocation:

```text
PORT A:
GPA0 LINE_FAR_LEFT
GPA1 LINE_LEFT
GPA2 LINE_CENTER
GPA3 LINE_RIGHT
GPA4 LINE_FAR_RIGHT
GPA5..7 RESERVED

PORT B:
GPB0 LED_LEFT
GPB1 LED_RIGHT
GPB2 BUZZER_CTRL
GPB3..7 RESERVED
```

### Error model

Driver shall distinguish at least:

```text
OK
NOT_FOUND
I2C_ERROR
```

No I2C failure may block forever.

### Acceptance criteria

- MCP detected at boot.
- Port A full-byte read works.
- Port B pin writes work.
- Missing MCP produces deterministic diagnostic.
- Robot motor safety remains independent from MCP state.
- Driver can be mocked for unit testing.

### Implementation / verification record

**Implementation commits:** `ab9b7a9933b021eb963919ac41f8eacc1446f34f` (driver/transport/tests/CI + BoardProfile allocation) and `6018e50a26fcd7dbc479a5aa627db6e86204a723` (full-suite runner syntax repair + CI syntax gate).

Implemented architecture:

- `MCP23017Driver` owns MCP23017 register semantics only.
- `IMCP23017Transport` is an injectable transport contract so the real driver can be unit tested without ESP32 hardware.
- `MCP23017WireTransport` is the production adapter over the shared System I2C bus and never initializes `Wire` itself.
- Address defaults to `BoardProfile::MCP23017::ADDRESS = 0x20`.
- BoardProfile now freezes MCP allocation: GPA0..4 = FL/L/C/R/FR and GPB0..2 = LED Left/LED Right/Buzzer.
- `begin()` probes the device and puts both ports into fail-safe input mode with pull-ups disabled before feature-specific ownership is configured.
- Error states are explicit: `OK`, `NOT_FOUND`, `I2C_ERROR`.
- Register operations are bounded by the shared System I2C timeout; the MCP layer contains no retry/blocking loop.
- Driver has no dependency on MotorSafety or motor output GPIO.
- `tests/v2_mcp23017/run_v2_mcp23017.py` compiles and executes the real C++ driver against a mock transport.
- Focused CI: `.github/workflows/v2-mcp23017-contract.yml`.
- Verification infrastructure regression in `run_all_tests.py` (literal `\\n`) was repaired while registering the MCP test.

Software verification covers:

- device present / deterministic `NOT_FOUND`;
- shared-bus unavailable / `I2C_ERROR`;
- Port A full-byte read;
- Port B full-byte read;
- input/output direction and pull-up configuration;
- pin read and output-latch pin write;
- invalid pin handling;
- injected read/write I2C failures;
- mockability using the production driver implementation;
- independence from motor safety;
- no new System I2C owner.
- GitHub Actions `V2 MCP23017 Contract` run `37406898368`: **PASS** on `6018e50a26fcd7dbc479a5aa627db6e86204a723`.
- GitHub Actions `V2 System I2C Contract` run `37406898412`: **PASS** on the same commit.
- GitHub Actions `V2 BoardProfile Contract` run `37406898381`: **PASS** on the same commit.
- MCP focused CI also validates `run_all_tests.py` with `python -m py_compile` before contract execution.

Hardware-dependent acceptance criteria:

- physical MCP detection at boot: `PENDING_HW`;
- physical Port A byte read: `PENDING_HW`;
- physical Port B output write: `PENDING_HW`;
- physical MCP + MPU6050 coexistence: `PENDING_HW`.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SW-002.

---

# 7. Milestone M2 — Motor Safety & ARM

## Goal

Motor output must be hardware-gated and independent from student program behavior.

---

## V2-SAFE-001 — MotorSafetyController

**Priority:** P0

### Requirement

Implement centralized motor safety state ownership.

Minimum conceptual states:

```text
BOOT
SAFE
ARMED
RUNNING
FAULT
```

Minimum API:

```cpp
begin()
arm()
disarm(reason)

isArmed()
isDriverEnabled()
```

Physical driver gate:

```text
GPIO4 -> TB6612 STBY
```

GPIO4 shall be LOW by default and remain LOW until explicitly armed.

### Motor output rule

Lowest common physical motor output path shall enforce:

```text
if !armed:
    requested PWM must not reach motor outputs
```

Safety shall not depend only on public API-level checks.

### Acceptance criteria

- Power-on boots in SAFE.
- STBY remains disabled before ARM.
- Non-zero motor command before ARM produces no physical motion.
- No alternate motion API can bypass the gate.
- Hardware configuration MOTOR OFF still works.

### Dependencies

V2-SW-001.

---

## V2-SAFE-002 — START / ARM Button

**Priority:** P0

### Requirement

Use:

```text
GPIO33
active-low
hardware pull-up / defined state
```

Software shall debounce START.

START transitions robot from:

```text
SAFE -> ARMED
```

Student code shall not directly arm the robot.

### Acceptance criteria

- START press required after every power cycle/reset.
- Holding/pressing START during boot shall not accidentally auto-run motors before system readiness.
- Student code calling motion APIs while SAFE remains physically blocked.
- START state is exposed to RobotHealth.

### Dependencies

V2-SAFE-001.

---

## V2-SAFE-003 — Fail-Safe Disarm Conditions

**Priority:** P0

### Requirement

Robot shall immediately disarm on:

```text
OTA start
critical battery
fatal platform fault
motor safety fault
watchdog/reset cycle
system reboot
explicit safety stop
```

ARMed state shall never persist across reboot.

OTA shall use:

```text
MotorSafety.disarm(OTA)
```

not only `RobotAPI::Stop()`.

### Acceptance criteria

- OTA always drives STBY inactive before firmware write.
- Reset returns to SAFE.
- Critical battery prevents new motion.
- Fatal error cannot leave driver enabled.
- OTA failure also leaves robot SAFE.

### Dependencies

V2-SAFE-001.

---

## V2-SAFE-004 — VM / Student Code Safety Boundary

**Priority:** P0

### Requirement

VM may execute after boot, but physical motor output shall remain blocked until robot is ARMED.

This preserves non-motion program execution while keeping safety independent from VM lifecycle.

### Acceptance criteria

- VM can execute sensor/logic code in SAFE.
- Motion commands are ignored/blocked at physical motor gate until ARM.
- Existing VM execution model does not require major redesign.

### Dependencies

V2-SAFE-001, V2-SAFE-002.

---

# 8. Milestone M3 — V2 Hardware Features

## Goal

Migrate V1 peripheral assumptions to V2 physical interfaces.

---

## V2-SW-004 — LineSensorBank 5CH

**Priority:** P1  
**Status:** PENDING_HW

### Requirement

Replace five independent direct-GPIO TCRT5000 reads with one 5-channel bank backed by MCP23017 Port A.

Minimum API:

```cpp
begin()
readMask()
channel(index)
healthy()
```

One control-cycle sample shall use one Port-A register read.

### Public logical channel mapping

Public API compatibility is frozen by Phase 0 Decision `P0-D01`:

```text
0 Left
1 Center
2 Right
3 Far Left
4 Far Right
```

`LineSensorBank` may use an internal physical index/order for MCP23017 access, but that internal order shall not change public API channel semantics.

### Canonical software bit contract

Canonical raw-mask compatibility is frozen by Phase 0 Decision `P0-D02`:

```text
bit4 bit3 bit2 bit1 bit0
 FL    L    C    R    FR
```

MCP23017 Port-A physical allocation remains:

```text
GPA0 LINE_FAR_LEFT
GPA1 LINE_LEFT
GPA2 LINE_CENTER
GPA3 LINE_RIGHT
GPA4 LINE_FAR_RIGHT
```

Therefore `LineSensorBank::readMask()` shall convert Port-A physical bits into the canonical software mask before returning it.

### Acceptance criteria

- `readMask()` returns stable 5-bit value.
- No five independent I2C transactions per control iteration.
- Missing MCP or line sensor subsystem returns health error instead of hanging.
- Feature flag OFF excludes active Line5 behavior.

### Implementation / verification record

**Implementation commits:** `012194f0c192f5fdbad96b04bcba6bd7ff680c9e` (LineSensorBank/MCP migration) and `49ab48ee9a26ec497d214fe0703b1e6ae6c73388` (regression alignment).

Implemented architecture:

- `LineSensorBank` is the V2 Line5 physical acquisition boundary.
- One `LineSensorBank::readMask()` performs one MCP23017 Port-A byte read and converts physical `GPA0..4 = FL,L,C,R,FR` into the frozen canonical software mask `bit4..0 = FL,L,C,R,FR`.
- Public channel semantics remain frozen as `0=L, 1=C, 2=R, 3=FL, 4=FR`.
- V1 direct-TCRT GPIO aliases were removed from `GPIO.h`; V2 no longer registers direct-GPIO TCRT5000 instances for Line5.
- `MCPLineSensor` preserves the existing TCRT5000/ISensor-facing diagnostic compatibility surface while sourcing state from LineSensorBank.
- `GetTraceRaw()` now uses exactly one LineSensorBank acquisition instead of iterating five direct sensors.
- Existing V1 line estimator/follower/intersection/recovery logic remains unchanged above the canonical mask boundary.
- MCP ownership is shared through `systemMCP23017()`; successful `MCP23017Driver::begin()` is idempotent so later V2 feature services do not reset MCP direction state.
- V1 Line5 compatibility regression was updated to validate logical/API compatibility rather than obsolete direct-GPIO ownership.
- `tests/v2_line_sensor_bank/run_v2_line_sensor_bank.py` compiles and executes the real C++ LineSensorBank + MCP driver against a fake transport.
- Test is registered in repository `run_all_tests.py`.

Software verification:

- physical GPA0..4 to canonical mask conversion: PASS;
- one Port-A read per `readMask()`: PASS;
- channel mapping 0..4: PASS;
- invalid channel deterministic false: PASS;
- I2C/read failure -> mask 0 + unhealthy: PASS;
- direct V1 Line5 GPIO aliases absent: PASS;
- V1 logical Line5 compatibility regression: PASS;
- MCP regression: PASS;
- GitHub Actions `V2 LineSensorBank Contract` run `37408109215`: **PASS** on `49ab48ee9a26ec497d214fe0703b1e6ae6c73388`;
- GitHub Actions `V2 BoardProfile Contract` run `37408109220`: **PASS** on the same commit.

Hardware-dependent acceptance criteria:

- physical MCP Port-A 5-channel sampling: `PENDING_HW`;
- TCRT5000 electrical polarity/active-level confirmation: `PENDING_HW`;
- missing-MCP runtime behavior on ESP32: `PENDING_HW`;
- control-loop timing/latency relative to V1 direct GPIO: deferred to `V2-TEST-005`, `PENDING_HW`.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SW-003.

---

## V2-SW-005 — Line5 Public API Compatibility

**Priority:** P1  
**Status:** DONE

### Requirement

Existing public line APIs shall remain supported.

The following APIs shall support 5 channels where applicable:

```text
ReadLine
GetTraceValue
GetTraceState
GetTraceRaw
LineBasis
LineFollow
LineMillisecond
LineIntersectionStop
LineTurnEncounterLine
LineForBmp
```

Legacy programs using center/left/right semantics shall continue to work.

### Acceptance criteria

- Existing 3-channel student programs remain functionally valid with `0=Left, 1=Center, 2=Right`.
- New channels remain appended as `3=Far Left, 4=Far Right`.
- `GetTraceRaw()` returns the canonical 5-bit mask `bit4..bit0 = FL,L,C,R,FR`.
- MCP23017 physical bit ordering does not leak into the public API.
- Hardware Requirement Validator continues to enforce `line_sensor`.

### Implementation / verification record

Compatibility contract is enforced by `tests/v2_line_api_compat/run_v2_line_api_compat.py` and dedicated CI `.github/workflows/v2-line-api-compat.yml`.

The regression freezes:

- public RobotAPI signatures for `ReadLine`, trace APIs and line behavior entry points;
- public channel IDs `0=L, 1=C, 2=R, 3=FL, 4=FR`;
- canonical `GetTraceRaw()` mask `bit4..0 = FL,L,C,R,FR`;
- MCP physical ordering remains hidden behind `LineSensorBank`;
- line feature OFF returns neutral values / safe behavior;
- compiler transports `read_line(0..4)`;
- Hardware Requirement Validator continues to require `line_sensor` for sensing and `motor + line_sensor` for line behaviors;
- public API documentation remains aligned with the frozen compatibility contract.

This requirement is a software/API compatibility contract. Physical sensor correctness is owned by `V2-SW-004` and remains `PENDING_HW` there; it is not duplicated as a blocker here.

Software verification evidence:

- implementation / contract commit: `96bee29fccf33977434fea11bc2c24e32eccabd6`;
- test-runner syntax repair: `229caf2b9c0cf8d21bf4d7bb88a7fe2b2b9620bb`;
- test import-path repair: `cb002336180edc03fb86f9f64a4c7872ee7ba070`;
- GitHub Actions `V2 Line API Compatibility` run `37409368909`: **PASS** on `cb002336180edc03fb86f9f64a4c7872ee7ba070`;
- upstream V1 logical Line5 regression: PASS inside the same workflow;
- V2 LineSensorBank regression: PASS inside the same workflow;
- public signatures, channel IDs, raw-mask contract, feature-OFF behavior, compiler channel transport, Hardware Requirement Validator and public docs: PASS.

**Verification status:** `VERIFIED_SW`  
**Task status:** `DONE`

### Dependencies

V2-SW-004.

---

## V2-SW-006 — Line5 Perception / Control Upgrade

**Priority:** P1

### Requirement

Preserve and adapt the V1 Line5 implementations already present in the frozen software baseline:

```text
LinePerception
LineErrorEstimator
IntersectionDetector
RecoveryStrategy
Line diagnostics
```

These components already use 5-channel semantics in the V1 frozen baseline. V2 work shall primarily migrate the acquisition path to `LineSensorBank`/MCP23017 and retain the canonical mask contract. Algorithm tuning is allowed only as an explicit follow-up requirement based on verification evidence.

Recommended weighted sensor positions:

```text
FL   L   C   R   FR
-2  -1   0  +1  +2
```

Required behaviors:

```text
center tracking
slight-left/right correction
strong-left/right correction
lost-line detection
line recovery
intersection/station pattern detection
```

### Acceptance criteria

Representative masks shall produce deterministic interpretation.

Minimum regression masks:

```text
00100
01100
11000
00011
00000
11111
```

Line response timing diagnostics shall remain available.

### Dependencies

V2-SW-004.

---

## V2-SW-007 — Servo HAL

**Priority:** P1

### Requirement

Replace current DUMMY Servo path with real PWM output.

Fixed mapping:

```text
Servo 1 -> GPIO16
Servo 2 -> GPIO17
```

Public API remains:

```text
set_servo(port, angle)
SetServo(port, angle)
```

Minimum behavior:

```text
port 1 -> Servo1
port 2 -> Servo2
angle clamp 0..180
```

### Acceptance criteria

- Real servo movement verified on both ports.
- Feature OFF prevents hardware drive.
- Invalid port handled deterministically.
- Servo implementation is isolated from VM/compiler internals.
- No Servo operation alters motor safety gate.

### Dependencies

V2-SW-001.

---

## V2-SW-008 — MCP23017 LED/Buzzer Migration

**Priority:** P1

### Requirement

Migrate:

```text
LED Left -> GPB0
LED Right -> GPB1
Buzzer -> GPB2
```

Public API remains compatible:

```text
Set3CLed
SetMp3Play
```

RobotAPI shall not directly manipulate MCP registers.

Introduce an auxiliary/status output abstraction.

### Acceptance criteria

- LEDs work through MCP.
- Buzzer works through MCP output + external driver.
- Feature guard for buzzer remains functional.
- MCP failure is reported through health but does not compromise motor safety.

### Dependencies

V2-SW-003.

---

## V2-SW-009 — Encoder V2 Board Integration

**Priority:** P1

### Requirement

Keep existing quadrature encoder implementation.

Freeze V2 physical mapping:

```text
GPIO34 Encoder L-A
GPIO35 Encoder L-B
GPIO36 Encoder R-A
GPIO39 Encoder R-B
```

### Acceptance criteria

- Existing encoder count/CPS/RPM APIs continue to work.
- Encoder feature ON/OFF behavior remains compatible.
- Line5 no longer shares encoder GPIO.
- Encoder data becomes available to RobotHealth/diagnostics.

### Dependencies

V2-SW-001.

---

# 9. Milestone M4 — Robot Health Platform

## Goal

Create one health source of truth consumed by HTTP, OLED, Serial and RoboStudio.

---

## V2-HLT-001 — BatteryMonitor

**Priority:** P1

### Requirement

Use:

```text
GPIO32 / ADC1
```

to measure battery pack voltage.

Health states:

```text
GOOD
LOW
CRITICAL
INVALID
```

Implementation shall include:

```text
sample filtering
calibration factor
hysteresis
invalid-reading detection
```

Initial V2 shall not expose fake high-precision SOC percentage.

### Acceptance criteria

- Stable voltage reading under normal load.
- LOW/CRITICAL does not chatter around thresholds.
- Calibration factor can be tuned.
- Invalid ADC readings are detectable.

### Dependencies

V2-SW-001.

---

## V2-HLT-002 — Critical Battery Safety Policy

**Priority:** P1

### Requirement

Battery LOW:

```text
warning
```

Battery CRITICAL:

```text
MotorSafety.disarm(LOW_BATTERY)
```

Servo policy shall be defined; recommended behavior is to block new high-load servo activity at CRITICAL.

### Acceptance criteria

- CRITICAL state guarantees motor disable.
- Returning briefly above threshold does not automatically re-arm.
- START must be required again after safety recovery/reset policy as defined.

### Dependencies

V2-HLT-001, V2-SAFE-001.

---

## V2-HLT-003 — ResetReasonService

**Priority:** P1

### Requirement

Capture ESP32 reset reason at boot.

Normalized values shall include at least:

```text
POWER_ON
SOFTWARE_RESET
WATCHDOG
BROWNOUT
PANIC
DEEP_SLEEP
UNKNOWN
```

### Acceptance criteria

- Reset reason is captured before normal runtime overwrites context.
- Brownout can be distinguished from normal software reset.
- Reset reason is exposed through RobotHealth and HTTP.

### Dependencies

None.

---

## V2-HLT-004 — RobotHealth Aggregate

**Priority:** P1

### Requirement

Create one source of truth:

```text
RobotHealthService
```

Minimum model:

```text
RobotHealth
├── system
│   ├── uptime
│   ├── reset_reason
│   ├── firmware_version
│   ├── board_profile
│   └── board_revision
│
├── battery
│   ├── voltage
│   └── state
│
├── motor
│   ├── armed
│   ├── enabled
│   ├── state
│   └── last_stop_reason
│
├── line
│   ├── available
│   ├── healthy
│   └── mask
│
├── encoder
│   ├── available
│   └── healthy
│
├── i2c
│   ├── healthy
│   └── mcp23017
│
└── network
    ├── connected
    ├── ip
    └── rssi
```

### Acceptance criteria

- HTTP, OLED and Serial consume the same health model.
- No duplicated battery/safety health logic in UI layers.
- Optional devices can report unavailable without making whole robot unhealthy.

### Dependencies

V2-SAFE-001, V2-HLT-001, V2-HLT-003, V2-SW-003.

---

## V2-NET-001 — `/api/v1/health` V2

**Priority:** P1

### Requirement

Extend existing endpoint while retaining compatibility-critical existing fields.

Existing fields to preserve:

```text
status
ready
robot_ready
network_ready
ota
hostname
ip
```

Add V2 health information.

Example:

```json
{
  "status": "ok",
  "ready": true,
  "robot_ready": true,
  "network_ready": true,
  "ota": true,
  "hostname": "robot-xxxx",
  "ip": "192.168.x.x",
  "board_profile": "antech_robot_v2",
  "battery": {
    "voltage": 7.52,
    "state": "GOOD"
  },
  "motor": {
    "armed": false,
    "enabled": false,
    "state": "SAFE"
  },
  "reset_reason": "BROWNOUT",
  "line_mask": 4,
  "i2c_ok": true,
  "rssi": -52
}
```

### Acceptance criteria

- Existing clients do not break due to removed old fields.
- V2 health fields come from RobotHealthService.
- Endpoint remains responsive when optional devices fail.
- Health endpoint shall not expose Wi-Fi/OTA secrets.

### Dependencies

V2-HLT-004.

---

## V2-HLT-005 — Local OLED Health Display

**Priority:** P2

### Requirement

OLED shall display minimum service information.

Normal example:

```text
ANTECH ROBOT
BAT GOOD 7.52V
WiFi OK
MOTOR SAFE
```

Fault example:

```text
FAULT
RESET BROWNOUT
BAT 6.30V
MOTOR LOCKED
```

OLED failure shall never stop robot runtime.

### Acceptance criteria

- OLED consumes RobotHealthService only.
- Display update is non-blocking enough for normal runtime.
- Missing OLED is treated as optional failure.

### Dependencies

V2-HLT-004, V2-SW-002.

---

# 10. Milestone M5 — RoboStudio V2 Integration

## Goal

Make RoboStudio aware of V2 physical board and Robot Health without exposing GPIO complexity to students.

---

## V2-CONF-001 — HardwareConfig V2 / Migration

**Priority:** P1

### Requirement

Introduce V2-aware configuration schema if board profile is persisted.

Recommended form:

```json
{
  "version": 2,
  "board_profile": "antech_robot_v2",
  "devices": {
    "motor": true,
    "encoder": false,
    "line_sensor": true,
    "ultrasonic": true,
    "imu": false,
    "servo": true,
    "buzzer": true
  }
}
```

Old v1 configuration shall be migrated or loaded through a deterministic compatibility policy.

### Acceptance criteria

- Existing user configuration is not silently lost.
- Unknown board profile fails clearly.
- Feature defaults remain deterministic.
- Generated feature macros continue to work.

### Dependencies

V2-SW-001.

---

## V2-RS-001 — RoboStudio Board Profile Awareness

**Priority:** P1

### Requirement

Hardware Configuration UI shall identify:

```text
Board: AnTech Robot V2
```

Students shall configure capabilities, not GPIO pins.

Board infrastructure shall not appear as normal student-selectable devices:

```text
MCP23017
Battery Monitor
Motor Safety
START
Robot Health
```

### Acceptance criteria

- User cannot remap physical pins.
- Device ON/OFF configuration remains simple.
- Board revision is visible for diagnostics/support.

### Dependencies

V2-CONF-001.

---

## V2-RS-002 — Robot Health Panel

**Priority:** P2

### Student view

Show only actionable status:

```text
Robot Connected
Battery GOOD / LOW
Motor SAFE / ARMED
Line Sensor OK
```

### Teacher/Diagnostic view

Show:

```text
battery voltage
reset reason
Wi-Fi RSSI
raw 5-bit line state
encoder count/status
motor armed/enabled
firmware version
board revision
uptime
I2C/MCP health
last stop reason
```

### Acceptance criteria

- Panel uses `/api/v1/health`.
- Network error is distinguishable from robot fault.
- Student view remains simple.
- Teacher view provides enough data to diagnose loose wire, low battery, brownout and sensor failure.

### Dependencies

V2-NET-001, V2-RS-001.

---

# 11. Milestone M6 — Verification & Release Hardening

## Goal

Prevent V2 hardware migration from breaking existing behavior or introducing unsafe states.

---

## V2-TEST-001 — Board Mapping Contract Tests

**Priority:** P0  
**Status:** DONE

Verify fixed mapping:

```text
Motor Safe = GPIO4
Servo1 = GPIO16
Servo2 = GPIO17
I2C SDA = GPIO21
I2C SCL = GPIO13
Battery = GPIO32
START = GPIO33
Encoder = GPIO34/35/36/39
MCP address = 0x20
```

Test must fail if physical contract changes accidentally.

### Implementation / verification record

- Implemented at `tests/v2_board_profile/run_v2_board_profile.py`.
- Registered in repository `run_all_tests.py`.
- Verifies stable profile ID, all frozen GPIO assignments, MCP23017 address, GPIO facade delegation, and that HardwareConfig/generated feature config do not own physical wiring.
- Focused software verification: PASS.
- C++11 BoardProfile compile/static-assert smoke verification: PASS.
- Hardware verification: not required for the software mapping contract; electrical/peripheral behavior is verified by dependent V2 tasks.

**Verification status:** `VERIFIED_SW`  
**Task status:** `DONE`

---

## V2-TEST-002 — MCP23017 Unit/Mock Tests

**Priority:** P0/P1  
**Status:** IN_PROGRESS

Test:

```text
device present
device missing
Port A read
Port B write
I2C error
timeout/recovery
Line mask conversion
```

### Implementation / verification record

Implemented now:

- device present / missing;
- Port A read;
- Port B read/write-path primitives;
- I2C read/write failure injection;
- shared-bus ownership regression;
- real C++ driver executed against mock transport.
- focused MCP CI PASS: run `37406898368`.

Still pending:

- physical timeout/recovery behavior: `PENDING_HW`;
- Line5 mask conversion: `VERIFIED_SW` by `V2-SW-004` / `tests/v2_line_sensor_bank`; physical verification remains `PENDING_HW`.

**Verification status:** `VERIFIED_SW`  
**Task status:** `IN_PROGRESS`

---

## V2-TEST-003 — Motor Safety Contract Tests

**Priority:** P0

Required cases:

```text
BOOT -> SAFE
motion before START -> blocked
START -> ARMED
OTA -> SAFE
critical battery -> SAFE
fault -> SAFE
reset -> SAFE
```

Hard requirement:

> No software path shall produce non-zero physical motor output while `armed == false`.

---

## V2-TEST-004 — Line5 Regression

**Priority:** P1

Representative masks:

```text
00100
01100
11000
00011
00000
11111
```

Test:

```text
perception
weighted error
recovery
intersection
station pattern
public API raw mask
```

---

## V2-TEST-005 — Line Response Performance

**Priority:** P1

Preserve existing diagnostic measurements:

```text
sensor read
control
motor submit
total latency
```

Compare V1 direct GPIO vs V2 MCP23017.

Acceptance threshold shall be set after first hardware measurement.

---

## V2-TEST-006 — Servo Regression

**Priority:** P1

Test:

```text
Servo1
Servo2
0 degrees
90 degrees
180 degrees
out-of-range clamp
invalid port
feature OFF
```

---

## V2-TEST-007 — Health Schema Contract

**Priority:** P1

Verify `/api/v1/health`:

- old compatibility fields remain;
- new V2 fields exist;
- invalid optional devices do not corrupt JSON;
- no credentials/secrets exposed.

---

## V2-TEST-008 — Hardware ON/OFF Matrix Extension

**Priority:** P1

Extend existing matrix for V2 features/configurations.

Minimum:

```text
Line ON/OFF
Encoder ON/OFF
Servo ON/OFF
IMU ON/OFF
Buzzer ON/OFF
Display optional ON/OFF if introduced
```

Board infrastructure remains fixed.

---

## V2-TEST-009 — Config Migration Regression

**Priority:** P1

Test:

```text
v1 config -> V2 load/migrate
v2 config -> save/reload
unknown board
unknown feature
missing device field
invalid version
```

---

## V2-TEST-010 — OTA Safety Regression

**Priority:** P0

Verify:

```text
armed robot
   |
OTA start
   |
STBY LOW
motor output 0
   |
update
   |
reboot
   |
SAFE
```

Robot shall never automatically re-arm after OTA.

---

## Development status rule

The backlog table below is a planning index. The authoritative completion rule is:

```text
implementation complete
    +
software verification recorded
    +
hardware verification recorded when applicable
    +
this source-of-truth updated
    =
task DONE
```

If hardware is unavailable, hardware-dependent criteria must remain `PENDING_HW`.

---

# 12. Full backlog summary

| Order | ID | Requirement | Priority | Milestone |
|---:|---|---|:---:|---|
| 1 | V2-SW-001 | Board Profile Contract — DONE | P0 | M1 |
| 2 | V2-SW-002 | System I2C Bus Manager — PENDING_HW | P0 | M1 |
| 3 | V2-SW-003 | MCP23017 Driver/HAL — PENDING_HW | P0 | M1 |
| 4 | V2-SAFE-001 | MotorSafetyController | P0 | M2 |
| 5 | V2-SAFE-002 | START/ARM Button | P0 | M2 |
| 6 | V2-SAFE-003 | Fail-Safe Disarm Conditions | P0 | M2 |
| 7 | V2-SAFE-004 | VM / Student Code Safety Boundary | P0 | M2 |
| 8 | V2-SW-004 | LineSensorBank 5CH — PENDING_HW | P1 | M3 |
| 9 | V2-SW-005 | Line5 Public API Compatibility — DONE | P1 | M3 |
| 10 | V2-SW-006 | Line5 Perception / Control Upgrade | P1 | M3 |
| 11 | V2-SW-007 | Servo HAL | P1 | M3 |
| 12 | V2-SW-008 | MCP LED/Buzzer Migration | P1 | M3 |
| 13 | V2-SW-009 | Encoder V2 Board Integration | P1 | M3 |
| 14 | V2-HLT-001 | BatteryMonitor | P1 | M4 |
| 15 | V2-HLT-002 | Critical Battery Safety Policy | P1 | M4 |
| 16 | V2-HLT-003 | ResetReasonService | P1 | M4 |
| 17 | V2-HLT-004 | RobotHealth Aggregate | P1 | M4 |
| 18 | V2-NET-001 | Health API V2 | P1 | M4 |
| 19 | V2-HLT-005 | OLED Health Display | P2 | M4 |
| 20 | V2-CONF-001 | HardwareConfig V2 / Migration | P1 | M5 |
| 21 | V2-RS-001 | RoboStudio Board Awareness | P1 | M5 |
| 22 | V2-RS-002 | Robot Health Panel | P2 | M5 |
| 23 | V2-TEST-001 | Board Mapping Contract Tests — DONE | P0 | M6 |
| 24 | V2-TEST-002 | MCP23017 Unit/Mock Tests — IN_PROGRESS | P0/P1 | M6 |
| 25 | V2-TEST-003 | Motor Safety Contract Tests | P0 | M6 |
| 26 | V2-TEST-004 | Line5 Regression | P1 | M6 |
| 27 | V2-TEST-005 | Line Response Performance | P1 | M6 |
| 28 | V2-TEST-006 | Servo Regression | P1 | M6 |
| 29 | V2-TEST-007 | Health Schema Contract | P1 | M6 |
| 30 | V2-TEST-008 | Hardware ON/OFF Matrix Extension | P1 | M6 |
| 31 | V2-TEST-009 | Config Migration Regression | P1 | M6 |
| 32 | V2-TEST-010 | OTA Safety Regression | P0 | M6 |

---

# 13. Recommended execution batches

## Batch A — Platform

```text
V2-SW-001
V2-SW-002
V2-SW-003
V2-TEST-001
V2-TEST-002
```

Exit criteria:

```text
Board V2 mapping stable
Shared I2C stable
MCP23017 stable
```

---

## Batch B — Safety

```text
V2-SAFE-001
V2-SAFE-002
V2-SAFE-003
V2-SAFE-004
V2-TEST-003
V2-TEST-010
```

Exit criteria:

```text
motor cannot move before ARM
OTA/reset/fault always return SAFE
```

No physical V2 robot shall be considered ready for student testing before Batch B passes.

---

## Batch C — Feature Migration

```text
V2-SW-004
V2-SW-005
V2-SW-006
V2-SW-007
V2-SW-008
V2-SW-009

V2-TEST-004
V2-TEST-005
V2-TEST-006
V2-TEST-008
```

Exit criteria:

```text
Line5 real
Servo real
LED/Buzzer via MCP
Encoder unchanged and stable
```

---

## Batch D — Health

```text
V2-HLT-001
V2-HLT-002
V2-HLT-003
V2-HLT-004
V2-NET-001
V2-HLT-005

V2-TEST-007
```

Exit criteria:

```text
Robot Health source of truth exists
Battery + reset + safety visible locally/remotely
```

---

## Batch E — RoboStudio

```text
V2-CONF-001
V2-RS-001
V2-RS-002
V2-TEST-009
```

Exit criteria:

```text
RoboStudio recognizes V2 board
student hardware config remains simple
teacher health diagnostics usable
```

---

# 14. Definition of V2 Software Ready

V2 software shall not be considered ready until all of the following are true:

1. V2 board mapping is frozen in software.
2. Shared I2C and MCP23017 are stable.
3. Motor hardware gate is implemented.
4. Robot always boots SAFE.
5. START required before motor enable.
6. OTA/reset/fault/critical battery disarm motor.
7. Line5 is fully operational.
8. Servo outputs are real, not DUMMY.
9. Encoder remains functional.
10. Battery voltage and reset reason are available.
11. RobotHealth is the common health source.
12. `/api/v1/health` exposes V2 state.
13. OLED can show local minimum health if installed.
14. RoboStudio recognizes board V2.
15. Student programs cannot bypass motor safety.
16. Safety regression tests pass.
17. Existing hardware capability/build-matrix behavior remains compatible.
18. No profile-dependent connector rewiring exists.

---

# 15. Architecture invariant

The following rules are mandatory for V2 software:

> **BoardProfile owns physical wiring. HardwareConfig owns feature enable/disable. Student code owns robot behavior. MotorSafetyController owns permission to physically move the robot. RobotHealthService owns health state. No upper software layer may bypass these ownership boundaries.**
