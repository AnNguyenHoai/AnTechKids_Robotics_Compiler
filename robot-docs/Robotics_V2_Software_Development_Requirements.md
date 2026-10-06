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
**Status:** PENDING_HW

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

### Implementation / verification record

Implemented architecture:

- `MotorSafetyController` is the centralized owner of conceptual states `BOOT`, `SAFE`, `ARMED`, `RUNNING`, and `FAULT`.
- minimum control API is implemented: `begin()`, `arm()`, `disarm(reason)`, `isArmed()`, `isDriverEnabled()`.
- `MotorSafetyGpioGate` owns physical TB6612 STBY control on `BoardProfile::Pins::MOTOR_SAFE_EN = GPIO4`.
- `begin()` configures GPIO4 output and drives it LOW before motor PWM pin initialization.
- successful `arm()` drives STBY HIGH only when `ROBOT_FEATURE_MOTOR != 0`.
- MOTOR feature OFF cannot enable STBY.
- fault-class disarm reasons transition the controller to `FAULT`; normal safety disarm reasons return to `SAFE`.
- `RobotAPI::_setMotorsRaw()` is the lowest common physical motor-output boundary and calls `allowPhysicalOutput(left,right)` before any non-zero PWM write.
- when not armed, requested non-zero motion is converted to four zero-duty writes; public/VM/line/heading paths cannot bypass the gate because all physical motor LEDC writes remain inside `_setMotorsRaw()`.
- zero-output commands remain allowed so PWM outputs can always be actively cleared while STBY is LOW.
- START/ARM input ownership is intentionally not implemented here; `V2-SAFE-002` will be the permitted runtime arm source.

Software regression:

- `tests/v2_motor_safety/run_v2_motor_safety.py` compiles and executes the real controller with a fake STBY gate;
- verifies BOOT->SAFE, arm, RUNNING, zero-command ARMED return, normal disarm, fault disarm, MOTOR-OFF behavior, GPIO4 ownership and no alternate physical PWM path;
- dedicated CI: `.github/workflows/v2-motor-safety-contract.yml`.

Hardware-dependent acceptance criteria:

- physical GPIO4/STBY LOW at boot/reset: `PENDING_HW`;
- physical TB6612 remains disabled for pre-ARM non-zero command: `PENDING_HW`;
- physical STBY HIGH enables motor driver after approved ARM path: `PENDING_HW`.

Software verification evidence:

- implementation commit: `07742a0fcfa4dc3c024c9d57be974ad093b4608b`;
- GitHub Actions `V2 Motor Safety Contract` run `37413076981`: **PASS**;
- GitHub Actions `V2 BoardProfile Contract` run `37413076806`: **PASS**;
- Battery, Encoder, System I2C, MCP23017, Auxiliary Outputs, Servo, Line API, LineSensorBank and Line Perception regressions remain green on the same commit lineage;
- host C++ regression validates BOOT/SAFE/ARMED/RUNNING/FAULT transitions, MOTOR-OFF behavior, normal/fault disarm and non-zero pre-ARM blocking.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SW-001.

---

## V2-SAFE-002 — START / ARM Button

**Priority:** P0  
**Status:** PENDING_HW

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

### Implementation / verification record

Implemented architecture:

- `StartArmController` is the sole production software owner allowed to call `MotorSafetyController::arm()`.
- `StartArmGpioInput` owns the START input on `BoardProfile::Pins::START_ARM = GPIO33`.
- GPIO33 is configured as active-low with `INPUT_PULLUP_MODE` to maintain a defined software input state; the physical external pull-up requirement remains hardware-owned.
- debounce interval is 30 ms.
- controller is initialized immediately after `RobotAPI::Initialize()`, while MotorSafety is still SAFE/STBY LOW.
- `onSystemReady()` explicitly re-samples START at the readiness boundary.
- if START is held at boot, pressed during setup, or held when readiness is declared, a stable release is mandatory before a later press can arm.
- a debounced press is accepted only when system readiness has been declared and MotorSafety state is exactly `SAFE`.
- holding START does not repeatedly arm; after any later disarm, a new release->press edge is required.
- MOTOR feature OFF remains non-armable through the approved START path.
- START update runs after the OTA-in-progress early-return check, so an active OTA transaction cannot create an ARM event.
- RobotAPI and VM expose no MotorSafety arm API; production `MotorSafetyController::arm()` is called only inside `StartArmController`.
- read-only `isPressed()`, `isReadyForPress()`, and `armedByStartThisBoot()` surfaces are available for later `V2-HLT-004` RobotHealth integration.

Software regression:

- `tests/v2_start_arm/run_v2_start_arm.py` compiles and executes the real START + MotorSafety controllers with fake input/gate;
- covers debounce, pre-ready press, held-at-boot, press-during-setup, release-before-arm, one-shot held press, re-arm edge, MOTOR OFF and student-surface isolation;
- dedicated CI: `.github/workflows/v2-start-arm-contract.yml`.

Hardware-dependent acceptance criteria:

- physical GPIO33 active-low electrical behavior / external defined-state network: `PENDING_HW`;
- physical switch bounce profile vs 30 ms debounce: `PENDING_HW`;
- held START through actual ESP32 boot/reset cannot enable TB6612: `PENDING_HW`;
- START state in RobotHealth aggregate: deferred to `V2-HLT-004`.

Software verification evidence:

- implementation commit: `b26b6965590ec4c1fca4faefb04730c31b56623f`;
- GitHub Actions `V2 START ARM Contract` run `37413758524`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37413758474`: **PASS**;
- BoardProfile, BatteryMonitor, Encoder, Servo, System I2C, MCP23017, Auxiliary Outputs, Line API and Line Perception regressions remain green on the same commit lineage;
- host C++ regression validates debounce, pre-ready/held-boot protection, release-before-arm, one-shot held press, re-arm edge, MOTOR-OFF behavior and student-surface isolation.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SAFE-001.

---

## V2-SAFE-003 — Fail-Safe Disarm Conditions

**Priority:** P0  
**Status:** IN_PROGRESS

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

### Implementation / verification record

Implemented fail-safe boundary:

- system lifecycle code uses `RobotMotorSafetyInternal::disarm(reason)`; this surface is intentionally not declared in public `RobotAPI.h` or VM/student APIs;
- the boundary first calls the internal motion stop path to write zero motor PWM/state, then calls `MotorSafetyController::disarm(reason)` to drive TB6612 STBY LOW;
- this ordering prevents stale PWM duty from causing immediate motion when a later approved START re-arms the driver.

Integrated disarm sources:

- ArduinoOTA start -> `disarm(OTA)`;
- HTTP OTA upload start -> `disarm(OTA)`;
- HTTP OTA successful reboot -> `disarm(REBOOT)` immediately before `ESP.restart()`;
- generated-program load fatal halt -> `disarm(FATAL_PLATFORM_FAULT)`;
- IMU startup fatal halt -> `disarm(FATAL_PLATFORM_FAULT)`;
- VM fatal error halt -> `disarm(FATAL_PLATFORM_FAULT)`;
- operator `safety stop` command -> `disarm(EXPLICIT_SAFETY_STOP)`.

OTA hardening:

- previously-existing ArduinoOTA callbacks are now registered with `ArduinoOTA.onStart/onEnd/onProgress/onError`;
- OTA failure/abort clears update state but never calls `arm()`; once OTA start disarms the robot, it remains SAFE until a new START release->press sequence;
- normal student `RobotAPI::Stop()` remains a motion stop and does not disarm, preserving expected lesson/program semantics.

Reset/watchdog/fault policy:

- `MotorSafetyController::begin()` always restores `SAFE`, STBY LOW and `RESET` reason after boot/reset;
- watchdog/fatal/motor-safety/low-battery disarm reasons remain fault-class and cannot be re-armed directly;
- `LOW_BATTERY` source integration is owned by `V2-HLT-002`;
- there is no dedicated motor-safety-fault detector in the current baseline; the reason/interface is ready, but detector integration remains a follow-up source requirement;
- watchdog reset-reason observation will be integrated with `V2-HLT-003`; boot still always returns physically SAFE regardless of reset reason.

Software regression:

- `tests/v2_fail_safe_disarm/run_v2_fail_safe_disarm.py` verifies clear-PWM-before-STBY ordering, OTA callbacks, HTTP/Arduino OTA safety, reboot ordering, fatal halt disarm, operator safety stop and absence of student disarm/arm surfaces;
- dedicated CI: `.github/workflows/v2-fail-safe-disarm.yml`.

Remaining acceptance:

- critical battery source -> `disarm(LOW_BATTERY)`: `VERIFIED_SW` by V2-HLT-002;
- physical STBY behavior during OTA/fatal/reboot/critical battery: `PENDING_HW`;
- watchdog/fatal reset reason exposure: deferred to `V2-HLT-003`;
- physical OTA failure/recovery remains SAFE: `PENDING_HW`.

Software verification evidence:

- implementation commit: `2ce40700210bbc6700df4750a72ef65d2ea50a82`;
- GitHub Actions `V2 Fail Safe Disarm Contract` run `37414318207`: **PASS**;
- GitHub Actions `V2 START ARM Contract` run `37414318344`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37414318107`: **PASS**;
- BatteryMonitor, Servo, MCP23017, System I2C, Encoder, Line API, LineSensorBank, Line Perception, BoardProfile and Auxiliary Output regressions remain green on the same commit lineage;
- regression verifies clear-PWM-before-STBY ordering, ArduinoOTA/HTTP OTA disarm, OTA failure persistence, reboot disarm before `ESP.restart()`, fatal halt disarm and explicit operator safety stop.

**Software verification status:** `VERIFIED_SW_PARTIAL`  
**Task status:** `IN_PROGRESS`

### Dependencies

V2-SAFE-001.

---

## V2-SAFE-004 — VM / Student Code Safety Boundary

**Priority:** P0  
**Status:** IMPLEMENTED

### Requirement

VM may execute after boot, but physical motor output shall remain blocked until robot is ARMED.

This preserves non-motion program execution while keeping safety independent from VM lifecycle.

### Acceptance criteria

- VM can execute sensor/logic code in SAFE.
- Motion commands are ignored/blocked at physical motor gate until ARM.
- Existing VM execution model does not require major redesign.

### Implementation / verification record

Implemented boundary:

- VM execution is intentionally independent from MotorSafety ARM state; the platform loop may continue stepping student logic while the robot is SAFE.
- VM has no dependency on `MotorSafetyController`, `RobotMotorSafetyInternal`, `systemMotorSafety()`, `arm()` or `disarm()`.
- motion opcodes dispatch only through the existing public `RobotAPI` surface;
- public `RobotAPI.h` exposes no MotorSafety controller, arm API, disarm reason or system-only safety boundary;
- `StartArmController` remains the only approved production owner of `MotorSafetyController::arm()`;
- the lowest common physical path `RobotAPI::_setMotorsRaw()` calls `systemMotorSafety().allowPhysicalOutput(...)` before any normal non-zero motor PWM write;
- blocked motion explicitly clears all four TB6612 PWM outputs to zero.

Software acceptance:

- `tests/v2_vm_safety_boundary/run_v2_vm_safety_boundary.py` compiles and executes the real `MotorSafetyController` and verifies SAFE blocks non-zero output while zero-output/software execution remains allowed;
- static integration checks verify VM logic/sensor dispatch is not ARM-gated, motion opcodes remain behind RobotAPI, student/VM surfaces cannot arm/disarm, and the real physical PWM path is safety-gated;
- the dedicated acceptance is registered in `run_all_tests.py`;
- focused CI: `.github/workflows/v2-vm-safety-boundary.yml`.

No separate hardware criterion is introduced by this task: physical STBY/PWM behavior is already owned by V2-SAFE-001 / V2-TEST-003. This task verifies the software ownership/bypass boundary.

**Software verification status:** `IMPLEMENTED_PENDING_CI`  
**Task status:** `IMPLEMENTED`

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
**Status:** PENDING_HW

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

### Implementation / verification record

V2 preserves the frozen V1 Line5 perception/control implementation rather than rewriting or tuning it without hardware evidence.

Software regression is implemented at `tests/v2_line_perception/run_v2_line_perception.py` and dedicated CI `.github/workflows/v2-line-perception-control.yml`.

Verified in software:

- weighted estimator positions remain `FL=-2, L=-1, C=0, R=+1, FR=+2`;
- representative masks are deterministic:
  - `00100` -> error `0.0`, `CENTER`;
  - `01100` -> error `-0.5`, `LEFT_CENTER`;
  - `11000` -> error `-1.5`, `LEFT`;
  - `00011` -> error `+1.5`, `RIGHT`;
  - `00000` -> `LOST`;
  - `11111` -> `INTERSECTION`;
- mask sanitization prevents non-Line5 high bits leaking into perception;
- `LineFollower` continues to use `LineErrorEstimator`, `IntersectionDetector`, `RecoveryStrategy`, PID reset on reacquire, and `LAST_DIRECTION_THRESHOLD=0.25`;
- recovery continues to search toward the last meaningful line direction and exits immediately on reacquire;
- existing line response diagnostics remain available for sensor/control/output/total timing.

Explicitly not changed without hardware evidence:

- intersection history length/threshold;
- current temporal policy where a sustained `6/6` candidate history does not assert intersection because the frozen implementation uses `candidates >= 3 && candidates < 6`;
- recovery phase speed tuning;
- center-zone-only reacquire policy;
- PID gains / motor mixing scale.

Requirement gap recorded:

- the frozen baseline contains no distinct `station pattern` classifier/service. Current pattern detection is `IntersectionDetector` only.
- V2-SW-006 does not invent a station algorithm silently. A separate station-pattern requirement must be defined if hardware/product behavior requires semantics beyond intersection detection.

Hardware-dependent acceptance criteria:

- real line tracking quality across center/slight/strong corrections: `PENDING_HW`;
- recovery effectiveness and phase tuning: `PENDING_HW`;
- intersection persistence/false-positive tuning: `PENDING_HW`;
- station-pattern semantics beyond current intersection detection: `PENDING_HW / REQUIREMENT_GAP`;
- line response latency acceptance threshold: `PENDING_HW` and tracked by `V2-TEST-005`.

Software verification evidence:

- implementation/regression commit: `024bfb812faa9039365c8b3eaed4e8dd9d6c2dc3`;
- temporal-policy regression correction: `3531d4d08fd388d7a70de761cc63924546ef5e07`;
- GitHub Actions `V2 Line Perception Control` run `37410091227`: **PASS** on `3531d4d08fd388d7a70de761cc63924546ef5e07`;
- the same workflow also passed V1 Line5 logical regression, V2 LineSensorBank regression, and V2 public Line API compatibility.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SW-004.

---

## V2-SW-007 — Servo HAL

**Priority:** P1  
**Status:** PENDING_HW

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

### Implementation / verification record

Implemented architecture:

- `ServoHAL` owns port mapping, angle clamp, pulse-to-duty conversion and lazy per-port PWM attachment.
- `IServoPwmTransport` makes the HAL testable without ESP32 hardware.
- `ServoLEDCTransport` is the production ESP32 adapter.
- Fixed BoardProfile mapping is preserved:
  - port 1 -> GPIO16;
  - port 2 -> GPIO17.
- Servo PWM contract is 50 Hz, 16-bit, initial software pulse mapping 500..2500 us for 0..180 degrees.
- `RobotAPI::SetServo(port, angle)` is no longer DUMMY; it remains feature-guarded by `ROBOT_FEATURE_SERVO`.
- Invalid ports are rejected deterministically without attaching or writing PWM.
- Feature OFF performs no ServoHAL/PWM operation.
- Servo HAL has no dependency on MotorSafety or drive-motor output pins.
- LEDC compatibility mapping reserves channels 4 and 5 for GPIO16/GPIO17; existing motor channels 0..3 remain unchanged.
- Compiler `ServoHandler.set_servo` now emits `Opcode::SetServo` instead of silently dropping the command.
- Existing VM `Opcode::SetServo` dispatch remains unchanged and calls `RobotAPI::SetServo`.
- `tests/v2_servo/run_v2_servo.py` compiles and runs the real C++ ServoHAL against a fake PWM transport and verifies compiler-to-VM transport.

Software verification covers:

- Servo1/Servo2 port mapping;
- 0/90/180 degree monotonic duty mapping;
- out-of-range clamp to 0/180;
- invalid-port rejection;
- lazy attach/no repeated attach per port;
- injected PWM attach/write failures;
- feature-OFF RobotAPI guard;
- compiler emits SetServo opcode;
- VM dispatch exists;
- independence from motor safety.

Hardware-dependent acceptance criteria:

- physical Servo1 movement on GPIO16: `PENDING_HW`;
- physical Servo2 movement on GPIO17: `PENDING_HW`;
- actual servo pulse endpoint/calibration validation: `PENDING_HW`;
- power/load behavior with the V2 electrical design: `PENDING_HW`.

Software verification evidence:

- implementation commit: `8346b93d0711327e37ebd7bc7c1680c81a767458`;
- host-test/include corrections and focused-gate retrigger: `e9a776594f9eb81a7509e9788894ae509f991798`, `82019c3e4dec96b9eb2fb2f281fa67c14fc7dfec`, `3aea89a8c8e064e8c1ffdb8dcb4485db3d478f79`;
- GitHub Actions `V2 Servo HAL Contract` run `37411071744`: **PASS** on `3aea89a8c8e064e8c1ffdb8dcb4485db3d478f79`;
- real C++ `ServoHAL` executed against mock PWM transport;
- compiler `set_servo` emits `Opcode::SetServo`;
- existing VM dispatch to `RobotAPI::SetServo` verified;
- feature-OFF and invalid-port behavior verified in software;
- no Servo HAL dependency on MotorSafety or motor wiring.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SW-001.

---

## V2-SW-008 — MCP23017 LED/Buzzer Migration

**Priority:** P1  
**Status:** IN_PROGRESS

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

### Implementation / verification record

Implemented architecture:

- `AuxOutputService` is the V2 auxiliary/status output abstraction over the shared `systemMCP23017()` instance.
- RobotAPI no longer owns direct LED/buzzer GPIO or MCP register logic.
- BoardProfile allocation is used:
  - GPB0 = LED Left;
  - GPB1 = LED Right;
  - GPB2 = Buzzer control.
- V1 `Set3CLed` parity semantics are preserved:
  - odd public port -> logical Right LED -> GPB1;
  - even public port -> logical Left LED -> GPB0.
- Non-positive LED ports are rejected deterministically.
- Each MCP output is initialized lazily. OLAT is primed LOW before switching the corresponding pin to output to avoid a startup-high pulse.
- `SetMp3Play(index)` preserves the existing fixed 200 ms beep approximation and now drives GPB2 through `AuxOutputService`.
- `ROBOT_FEATURE_BUZZER=0` returns before any buzzer-output initialization/write.
- Legacy direct aliases `OUTPUT_LED_LEFT_PIN`, `OUTPUT_LED_RIGHT_PIN`, and `OUTPUT_BUZZER_PIN` are removed from `GPIO.h`.
- Compiler/VM transport for `Set3CLed` and `SetMp3Play` remains unchanged.
- Auxiliary output code has no MotorSafety/motor-output dependency.
- `AuxOutputService::healthy()` / `lastError()` expose MCP failure state for later `V2-HLT-004 RobotHealthService` integration.

Software verification is implemented at `tests/v2_aux_output/run_v2_aux_output.py` with dedicated CI `.github/workflows/v2-mcp-aux-output.yml`.

Acceptance split:

- LED/Buzzer migration, feature guard, public compatibility and failure propagation are software-verifiable here.
- Physical LED/buzzer operation remains `PENDING_HW`.
- Requirement “MCP failure is reported through health” is integration-owned by `V2-HLT-004`; this task provides the health-ready status surface but does not invent RobotHealth early.

Software verification evidence:

- implementation commit: `93ed976e7987f6b4df54197eb812611d9ac4927f`;
- direct-startup-GPIO cleanup / BoardProfile regression alignment: `bdbe82a4d0228772bd774209375fed898e72e580`;
- GitHub Actions `V2 MCP Auxiliary Outputs` run `37411547214`: **PASS** on `bdbe82a4d0228772bd774209375fed898e72e580`;
- GitHub Actions `V2 BoardProfile Contract` run `37411547251`: **PASS** on the same commit;
- GitHub Actions `V2 System I2C Contract` run `37411547282`: **PASS** on the same commit;
- existing LineSensorBank, Line Perception and Servo regressions also remain green on the same implementation lineage.

Remaining acceptance:

- physical LED Left/Right behavior via GPB0/GPB1: `PENDING_HW`;
- physical buzzer control via GPB2 + external driver: `PENDING_HW`;
- RobotHealth reporting of auxiliary/MCP failure: deferred integration to `V2-HLT-004` (service exposes `healthy()/lastError()` now).

**Software verification status:** `VERIFIED_SW`  
**Task status:** `IN_PROGRESS`

### Dependencies

V2-SW-003.

---

## V2-SW-009 — Encoder V2 Board Integration

**Priority:** P1  
**Status:** IN_PROGRESS

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

### Implementation / verification record

The existing `Encoder` quadrature driver is retained unchanged and the V2 integration is frozen around the BoardProfile mapping:

- Left A = GPIO34;
- Left B = GPIO35;
- Right A = GPIO36;
- Right B = GPIO39.

Software contract:

- RobotAPI continues to construct the left/right encoders from BoardProfile-backed GPIO aliases;
- existing count, CPS, RPM, reset, CPR and inversion APIs remain unchanged;
- `ROBOT_FEATURE_ENCODER=0` retains callable neutral/no-op fallbacks;
- initialization is feature-guarded;
- Line5 direct-GPIO aliases are absent, so Line5 no longer shares GPIO34/35 with encoders;
- serial diagnostics continue to expose count/CPS/RPM/CPR/inverted data;
- RobotHealth integration is owned by `V2-HLT-004`; V2-SW-009 preserves the encoder query surface required by that aggregate.

Verification strategy:

- `tests/v2_encoder/run_v2_encoder.py` compiles and executes the real `Encoder.cpp` against a fake Arduino GPIO/interrupt environment;
- regression covers quadrature edge count, CPS, RPM, direction, inversion, reset and CPR configuration;
- dedicated CI: `.github/workflows/v2-encoder-contract.yml`.

Known implementation debt intentionally not changed without hardware evidence:

- `Encoder.cpp` and `Sensor/QuadratureDecoder.h` currently encode opposite sign conventions for the same quadrature sequence.
- V2-SW-009 freezes the existing `Encoder.cpp` behavior to avoid silently reversing physical wheel direction. Consolidation requires physical direction verification.

Acceptance split:

- mapping/API/feature/diagnostic compatibility: software-verifiable here;
- physical count direction, signal quality and RPM calibration: `PENDING_HW`;
- RobotHealth aggregation: deferred to `V2-HLT-004`.

Software verification evidence:

- regression/source-of-truth commit: `7f643bdbc326cf89163cb2287b7e6978c2d638c4`;
- GitHub Actions `V2 Encoder Contract` run `37412125165`: **PASS**;
- GitHub Actions `V2 BoardProfile Contract` run `37412125220`: **PASS**;
- GitHub Actions `V2 Servo HAL Contract` run `37412125291`: **PASS**;
- GitHub Actions `V2 MCP23017 Contract` run `37412125076`: **PASS**;
- GitHub Actions `V2 System I2C Contract` run `37412125229`: **PASS**;
- GitHub Actions `V2 MCP Auxiliary Outputs` run `37412125167`: **PASS**;
- GitHub Actions `V2 Line Perception Control` run `37412125143`: **PASS**;
- GitHub Actions `V2 Line API Compatibility` run `37412125140`: **PASS**.

Remaining acceptance:

- physical count direction on left/right wheels: `PENDING_HW`;
- encoder electrical signal quality/noise: `PENDING_HW`;
- actual counts-per-revolution calibration: `PENDING_HW`;
- RobotHealth encoder availability/health aggregation: deferred to `V2-HLT-004`.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `IN_PROGRESS`

### Dependencies

V2-SW-001.

---

# 9. Milestone M4 — Robot Health Platform

## Goal

Create one health source of truth consumed by HTTP, OLED, Serial and RoboStudio.

---

## V2-HLT-001 — BatteryMonitor

**Priority:** P1  
**Status:** PENDING_HW

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

### Implementation / verification record

Implemented architecture:

- `BatteryMonitor` owns filtering, calibrated voltage conversion, health-state classification and hysteresis.
- `IBatteryAdcSource` makes the monitor host-testable.
- `ArduinoBatteryAdcSource` is the production adapter and reads only `BoardProfile::Pins::BATTERY_ADC = GPIO32` through the GPIO HAL.
- Health states are exactly `GOOD`, `LOW`, `CRITICAL`, `INVALID`.
- Each sample uses a configurable multi-sample arithmetic filter.
- Calibration factor, LOW threshold, CRITICAL threshold, hysteresis, sample count and raw-validity window are configurable.
- Raw readings at/beyond the configured validity boundaries are reported `INVALID`.
- LOW and CRITICAL recovery require crossing their threshold plus hysteresis, preventing threshold chatter.
- No SOC/percentage estimate is exposed.
- Legacy `Diagnostic::checkBattery()` no longer reads GPIO34 or assumes a hard-coded 2:1 divider; it consumes `systemBatteryMonitor()`.

Calibration/threshold governance:

- repository hardware docs identify a 7.5 V battery pack, but the V2 requirements/hardware docs do not define the GPIO32 resistor-divider ratio or approved LOW/CRITICAL thresholds;
- therefore production `BatteryMonitorConfig` defaults to `calibrationValid=false`;
- until hardware values are measured/approved, production sampling reports `INVALID` rather than publishing a false battery-pack voltage/state;
- host regression injects an explicit synthetic calibration config to verify the algorithm independently of board-specific values.

Software regression:

- `tests/v2_battery_monitor/run_v2_battery_monitor.py` compiles and executes the real `BatteryMonitor.cpp`;
- covers sample averaging, calibration factor, GOOD/LOW/CRITICAL classification, LOW/CRITICAL hysteresis, invalid raw readings and uncalibrated fail-safe behavior;
- dedicated CI: `.github/workflows/v2-battery-monitor-contract.yml`.

Hardware-dependent acceptance criteria:

- GPIO32 divider ratio/calibration factor: `PENDING_HW`;
- approved LOW/CRITICAL thresholds: `PENDING_HW`;
- stable pack-voltage reading under normal motor/servo load: `PENDING_HW`;
- invalid/open/saturated ADC behavior on the physical board: `PENDING_HW`.

Software verification evidence:

- implementation commit: `12125c2a93397d80e999d9c85f219d89f4dc6f9b`;
- host-test construction correction: `5ef0ab938a1062f6b515326247600f43c5dfbb62`;
- GitHub Actions `V2 Battery Monitor Contract` run `37412705047`: **PASS** on `5ef0ab938a1062f6b515326247600f43c5dfbb62`;
- focused workflow also passes BoardProfile and Encoder regressions;
- host C++ regression validates filtering, calibration factor, GOOD/LOW/CRITICAL classification, hysteresis, raw invalid detection and fail-safe uncalibrated behavior;
- obsolete GPIO34 battery ADC diagnostic path is removed.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-SW-001.

---

## V2-HLT-002 — Critical Battery Safety Policy

**Priority:** P1  
**Status:** PENDING_HW

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

### Implementation / verification record

Implemented policy:

- `BatterySafetyPolicy` samples `BatteryMonitor` on a bounded 250 ms cadence.
- LOW emits a warning event but does not disarm the motor driver.
- CRITICAL latches battery safety, routes through `RobotMotorSafetyInternal::disarm(LOW_BATTERY)`, clears motor PWM before STBY LOW, and blocks new servo commands.
- servo policy is explicitly defined for V2: new `SetServo()` activity is blocked while the CRITICAL battery latch is active; LOW does not block servo.
- INVALID is not silently treated as CRITICAL because V2-HLT-001 production calibration remains intentionally invalid until divider/threshold values are approved.
- if a CRITICAL latch is already active and a later sample becomes INVALID, the latch remains active and servo remains blocked.
- BatteryMonitor hysteresis owns electrical recovery. Only after the monitor exits CRITICAL to LOW/GOOD does the policy attempt fault recovery.
- `MotorSafetyController::recoverFaultToSafe(LOW_BATTERY)` is reason-specific and transitions only matching `FAULT -> SAFE`; it never enables STBY and never arms the robot.
- after battery recovery, a new approved START press is required for `SAFE -> ARMED`.
- another fault reason such as `FATAL_PLATFORM_FAULT` cannot be cleared by battery recovery.
- battery safety evaluation runs before START processing in the main loop, so a same-loop CRITICAL condition wins over an arm request.

Software regression:

- `tests/v2_battery_safety/run_v2_battery_safety.py` compiles and executes the real `BatteryMonitor`, `BatterySafetyPolicy`, and `MotorSafetyController`;
- covers LOW warning, CRITICAL disarm, critical hysteresis, FAULT->SAFE recovery without auto-arm, START-required semantics, servo blocking, INVALID-before-critical behavior, INVALID-after-critical latch persistence, and reason-specific recovery;
- dedicated CI: `.github/workflows/v2-critical-battery-safety.yml`.

Hardware-dependent acceptance criteria:

- actual LOW/CRITICAL thresholds and hysteresis are still `PENDING_HW` under V2-HLT-001 calibration;
- physical CRITICAL voltage must force GPIO4/STBY LOW: `PENDING_HW`;
- recovery above the measured hysteresis must leave the robot SAFE until START: `PENDING_HW`;
- servo power/load behavior under low/critical battery requires physical validation: `PENDING_HW`.

Software verification evidence:

- implementation commit: `6a921788eee3ddf3cc097fc23ffc619bd42febb4`;
- GitHub Actions `V2 Critical Battery Safety` run `37415009778`: **PASS**;
- GitHub Actions `V2 Fail Safe Disarm Contract` run `37415009856`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37415009755`: **PASS**;
- GitHub Actions `V2 Battery Monitor Contract` run `37415009791`: **PASS**;
- GitHub Actions `V2 START ARM Contract` run `37415009735`: **PASS**;
- GitHub Actions `V2 Servo HAL Contract` run `37415009781`: **PASS**;
- BoardProfile, MCP23017, Line API and Line Perception regressions remain green on the same implementation lineage;
- host C++ regression verifies LOW warning, CRITICAL latch/disarm, hysteretic recovery to SAFE without auto-arm, invalid-reading policy, reason-specific fault recovery and servo blocking.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

### Dependencies

V2-HLT-001, V2-SAFE-001, V2-SAFE-003.

---

## V2-HLT-003 — ResetReasonService

**Priority:** P1  
**Status:** IMPLEMENTED

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

### Implementation / verification record

Implemented architecture:

- `ResetReasonService` captures the boot reset cause exactly once and exposes normalized read-only state for later RobotHealth/HTTP consumption.
- `Esp32ResetReasonSource` is the production ESP32 adapter and uses `esp_reset_reason()`.
- normalized values are:
  - `POWER_ON`;
  - `SOFTWARE_RESET`;
  - `WATCHDOG`;
  - `BROWNOUT`;
  - `PANIC`;
  - `DEEP_SLEEP`;
  - `UNKNOWN`.
- ESP32 watchdog variants `ESP_RST_INT_WDT`, `ESP_RST_TASK_WDT`, and `ESP_RST_WDT` normalize to `WATCHDOG`.
- `ESP_RST_BROWNOUT` remains distinct from `ESP_RST_SW`.
- capture occurs in `setup()` before `RobotAPI::Initialize()`, diagnostics, VM, network, or other normal runtime initialization can overwrite contextual state.
- capture is one-shot; later calls cannot replace the recorded boot reason.

Safety integration:

- `MotorSafetyController::setBootSafetyContext(reason)` records safety-relevant boot context while forcing driver disabled and preserving `SAFE`.
- when reset reason is `WATCHDOG`, main boot flow records `MotorDisarmReason::WATCHDOG` after MotorSafety initialization.
- watchdog reboot therefore remains `SAFE` / STBY LOW and requires a fresh START press; it does not boot into FAULT and does not auto-arm.
- other normalized reset reasons remain available to RobotHealth without inventing a motor fault policy.

Software regression:

- `tests/v2_reset_reason/run_v2_reset_reason.py` compiles and executes the real `ResetReasonService` and `MotorSafetyController`;
- covers every normalized reason, one-shot capture, ESP32 mapping contract, brownout/software distinction, boot capture ordering and watchdog SAFE context;
- dedicated CI: `.github/workflows/v2-reset-reason-contract.yml`.

Remaining integration:

- expose reset reason through `RobotHealthService`: owned by `V2-HLT-004`;
- expose through HTTP: owned by `V2-NET-001`;
- physical reset-cause acceptance on real ESP32 for brownout/watchdog/panic/deep-sleep remains `PENDING_HW`.

Software verification evidence:

- implementation commit: `956660d772c1868ee51d0a221ea7065a2a83d1de`;
- GitHub Actions `V2 Reset Reason Contract` run `37416220137`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37416220005`: **PASS**;
- GitHub Actions `V2 Fail Safe Disarm Contract` run `37416220211`: **PASS**;
- GitHub Actions `V2 START ARM Contract` run `37416220086`: **PASS**;
- GitHub Actions `V2 Critical Battery Safety` run `37416220065`: **PASS**;
- GitHub Actions `V2 Battery Monitor Contract` run `37416220031`: **PASS**;
- host C++ regression verifies all normalized reset values, one-shot capture, brownout/software distinction, watchdog SAFE context and fresh-START requirement after watchdog reboot.

Hardware acceptance still pending:

- induce and verify physical brownout reset reporting;
- induce and verify physical watchdog reset reporting;
- verify panic/deep-sleep reporting on real ESP32 where applicable.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `IMPLEMENTED`

### Dependencies

None.

---

## V2-HLT-004 — RobotHealth Aggregate

**Priority:** P1  
**Status:** IN_PROGRESS

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

### Implementation / verification record

Implemented architecture:

- `RobotHealthService` is the single aggregate owner of the current `RobotHealth` snapshot.
- the minimum V2 model is implemented for:
  - system: uptime, reset reason, firmware version, board profile, board revision;
  - battery: voltage, state;
  - motor: armed, enabled, safety state, last stop/disarm reason;
  - START: pressed, ready-for-press, armed-by-START-this-boot;
  - line: available, healthy, cached 5-bit mask;
  - encoder: available, healthy;
  - System I2C: healthy, MCP23017 health;
  - network: connected, IP, RSSI.
- `RobotHealthPlatformSource` is the production adapter that reads the existing subsystem owners.
- health refresh is intentionally read-only:
  - it does not trigger a BatteryMonitor ADC sample;
  - it does not perform a new Line5 MCP read;
  - it does not initialize/probe MCP23017;
  - it does not arm/disarm or otherwise mutate safety state.
- `RobotHealthInputsInternal` bridges Line/Encoder runtime health without adding those health internals to public RobotAPI/VM surfaces.
- Encoder initialization success is retained explicitly for aggregate health instead of assuming feature ON means healthy.
- network IP/RSSI are exposed read-only by RobotNetworkService; Wi-Fi ownership remains inside the network service.
- BoardProfile ID/revision and RobotIdentity firmware version are reused rather than duplicated.

Consumer migration:

- Serial `robot status` now consumes `systemRobotHealth().refresh()` for system, battery, motor, START, Line, Encoder, I2C/MCP and network health.
- existing HTTP `/api/v1/health` is intentionally not migrated in this task; schema/compatibility migration belongs to `V2-NET-001`.
- OLED is not present in the current baseline; `V2-HLT-005` must consume RobotHealthService when implemented.

Optional-device semantics:

- disabled Line/Encoder report `available=false` / `healthy=false` without changing unrelated health fields;
- optional-device unavailability does not mutate battery, motor, network, or system health.

Software regression:

- `tests/v2_robot_health/run_v2_robot_health.py` compiles and executes the real aggregate service with an injected source and verifies the minimum model, read-only production aggregation, internal Line/Encoder bridge, Serial migration and HTTP scope boundary;
- dedicated CI: `.github/workflows/v2-robot-health-aggregate.yml`.

Remaining acceptance:

- HTTP consumes RobotHealthService: `VERIFIED_SW` by `V2-NET-001`;
- OLED software controller consumes RobotHealthService only: `VERIFIED_SW` by V2-HLT-005; concrete OLED transport is BLOCKED by missing hardware contract;
- physical health values remain subject to their subsystem `PENDING_HW` acceptance.

Software verification evidence:

- implementation commit: `b8a5cc31d676c27a6719da45a53b0816151cb168`;
- GitHub Actions `V2 Robot Health Aggregate` run `37416808206`: **PASS**;
- GitHub Actions `V2 Reset Reason Contract` run `37416808056`: **PASS**;
- GitHub Actions `V2 Critical Battery Safety` run `37416807962`: **PASS**;
- GitHub Actions `V2 Battery Monitor Contract` run `37416808098`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37416808039`: **PASS**;
- GitHub Actions `V2 Encoder Contract` run `37416808019`: **PASS**;
- GitHub Actions `V2 LineSensorBank Contract` run `37416808037`: **PASS**;
- GitHub Actions `V2 Line API Compatibility` run `37416807982`: **PASS**;
- GitHub Actions `V2 System I2C Contract` run `37416808082`: **PASS**;
- GitHub Actions `V2 MCP23017 Contract` run `37416808118`: **PASS**;
- GitHub Actions `V2 MCP Auxiliary Outputs` run `37416808079`: **PASS**;
- GitHub Actions `V2 Servo HAL Contract` run `37416808032`: **PASS**;
- host C++ regression verifies the aggregate model independently through an injected source;
- static regression verifies production refresh is read-only, Line/Encoder internals do not leak into public RobotAPI, Serial uses the aggregate, and HTTP remains explicitly deferred to V2-NET-001.

**Software verification status:** `VERIFIED_SW_PARTIAL`  
**Task status:** `IN_PROGRESS`

### Dependencies

V2-SAFE-001, V2-HLT-001, V2-HLT-003, V2-SW-003.

---

## V2-NET-001 — `/api/v1/health` V2

**Priority:** P1  
**Status:** IMPLEMENTED

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

### Implementation / verification record

Implemented architecture:

- `RobotNetworkService::sendHealth()` now refreshes exactly one `RobotHealthService` snapshot and delegates JSON generation to `RobotHealthJsonSerializer`.
- V2 subsystem health is not recomputed in the HTTP layer.
- serializer is a deterministic, hardware-independent transformation from `RobotHealth` + compatibility fields to JSON.
- JSON string values are escaped before emission.

Compatibility-critical top-level fields preserved:

- `status`;
- `ready`;
- `robot_ready`;
- `network_ready`;
- `ota`;
- `hostname`;
- `ip`.
- existing `http_ota` is also retained.

V2 fields added from RobotHealthService:

- `uptime_ms`;
- `firmware_version`;
- `board_profile`;
- `board_revision`;
- `reset_reason`;
- `battery { voltage, state }`;
- `motor { armed, enabled, state, last_stop_reason }`;
- `start { pressed, ready_for_press, armed_by_start_this_boot }`;
- `line { available, healthy, mask }` plus compatibility/convenience `line_mask`;
- `encoder { available, healthy }`;
- `i2c { healthy, mcp23017 }` plus compatibility/convenience `i2c_ok`;
- `rssi`.

Resilience/security contract:

- optional devices serialize their `available/healthy` state and do not block the endpoint;
- HTTP serialization performs no direct ADC, Line5, MCP23017, MotorSafety, START, or I2C hardware operations;
- endpoint and serializer do not access/expose SSID, Wi-Fi password, OTA password, Authorization, or Basic Auth credentials;
- health remains responsive based on the already-collected aggregate snapshot.

Software regression:

- `tests/v2_health_http/run_v2_health_http.py` compiles and runs the real serializer, parses its output with a JSON parser, and verifies old fields, V2 fields, escaping, optional-device behavior, aggregate-only ownership, and secret exclusion;
- dedicated CI: `.github/workflows/v2-health-http-contract.yml`.

Software verification evidence:

- implementation commit: `a72b35f030b52b28c4e449000257eca5f22d1bd4`;
- HLT-004 transition-regression alignment: `ed806568ec5d68e34c305dcc7c58fff8a65168ca`;
- GitHub Actions `V2 Health HTTP Contract` run `37417762294`: **PASS**;
- GitHub Actions `V2 Robot Health Aggregate` run `37417762355`: **PASS**;
- serializer C++ was compiled and executed in CI; emitted payload was parsed with a JSON parser;
- compatibility-critical V1 fields, V2 aggregate fields, string escaping, optional-device serialization, aggregate-only ownership and secret exclusion were all verified.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `IMPLEMENTED`

### Dependencies

V2-HLT-004.

---

## V2-HLT-005 — Local OLED Health Display

**Priority:** P2  
**Status:** BLOCKED

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

### Implementation / verification record

Software-side display architecture is implemented without inventing an undefined OLED hardware contract:

- `ILocalHealthDisplay` defines the optional display transport boundary.
- `LocalHealthDisplayFormatter` formats only a supplied `RobotHealth` snapshot.
- `LocalHealthDisplayController` consumes `RobotHealthService` only and updates on a bounded 500 ms cadence.
- normal frame matches the requirement intent:
  - `ANTECH ROBOT`;
  - battery state/voltage;
  - Wi-Fi OK/OFF;
  - motor safety state.
- current-fault frame is selected when motor state is `FAULT` or battery state is `CRITICAL` and includes:
  - `FAULT`;
  - normalized reset reason;
  - battery state/voltage;
  - motor LOCKED/ENABLED.
- missing display is optional: failed `begin()` causes no health refresh/render attempt and robot runtime continues.
- a runtime render failure disables future display attempts but does not stop robot execution or mutate health/safety state.
- `main.ino` integrates display begin/update without making readiness or control flow depend on display availability.
- `NullLocalHealthDisplay` is the current production transport because no real OLED hardware contract exists.

Hardware-contract gap:

- current hardware docs only list “OLED Display” as a planned module;
- no OLED controller/model is specified;
- no I2C address is specified;
- no display geometry is specified;
- no power/electrical contract is specified;
- no driver/library dependency is specified in `platformio.ini`;
- therefore this task must not silently choose SSD1306/SH1106, address 0x3C/0x3D, or a third-party library.

Software regression:

- `tests/v2_local_health_display/run_v2_local_health_display.py` compiles and executes the real formatter/controller with fake RobotHealth source/display;
- verifies normal/fault content, bounded update cadence, RobotHealth-only consumption, missing-display optional behavior, runtime render failure handling and absence of invented OLED hardware assumptions;
- dedicated CI: `.github/workflows/v2-local-health-display.yml`.

Closure condition:

- define/freeze OLED model/controller, System-I2C address, geometry, power/electrical requirements and approved firmware driver/library;
- then replace `NullLocalHealthDisplay` with the concrete optional System-I2C adapter and perform physical validation.

Software verification evidence:

- implementation commit: `24db53caa129dd2e33fbbe6edfb75b14ec5b53d4`;
- GitHub Actions `V2 Local Health Display` run `37418270940`: **PASS**;
- GitHub Actions `V2 Robot Health Aggregate` run `37418270966`: **PASS**;
- GitHub Actions `V2 Health HTTP Contract` run `37418271023`: **PASS**;
- GitHub Actions `V2 System I2C Contract` run `37418270920`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37418270957`: **PASS**;
- host C++ regression validates required normal/fault frames, 500 ms bounded refresh cadence, missing-display fail-open behavior, runtime render-failure isolation, RobotHealth-only consumption, and absence of invented OLED model/address/library assumptions.

**Software foundation status:** `VERIFIED_SW`  
**Task status:** `BLOCKED` — `REQUIREMENT_GAP / PENDING_HW_CONTRACT`

### Dependencies

V2-HLT-004, V2-SW-002.

---

# 10. Milestone M5 — RoboStudio V2 Integration

## Goal

Make RoboStudio aware of V2 physical board and Robot Health without exposing GPIO complexity to students.

---

## V2-CONF-001 — HardwareConfig V2 / Migration

**Priority:** P1  
**Status:** IMPLEMENTED

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

### Implementation / verification record

Implemented schema contract:

- current schema version is `2`;
- frozen board profile is `antech_robot_v2`;
- shipped `robostudio/config/hardware.json` now persists:
  - `version: 2`;
  - `board_profile: antech_robot_v2`;
  - capability-only `devices` flags.
- both RoboStudio domain code and deployment/runtime tools use the same schema constants and deterministic migration policy.

V1 compatibility policy:

- V1 (`version: 1`) has no persisted board profile;
- V1 is accepted and migrated in memory to schema V2 with `board_profile=antech_robot_v2`;
- every existing known device selection is preserved exactly;
- missing registered devices still receive deterministic registry defaults;
- loading a V1 file does not silently rewrite the file;
- the next explicit save writes schema V2.

V2 validation:

- V2 requires `board_profile`;
- any V2 board profile other than `antech_robot_v2` fails clearly;
- unsupported schema versions fail clearly;
- unknown devices remain rejected.

Physical/capability separation:

- generated `ROBOT_FEATURE_*` macros continue to represent capability ON/OFF only;
- generated headers do not contain `board_profile`, GPIO numbers, or BoardProfile pin ownership;
- `BoardProfile.h` remains the sole firmware physical-wiring source of truth;
- changing a feature flag cannot remap a connector.

Software regression:

- `tests/v2_hardware_config/run_v2_hardware_config.py` verifies V1->V2 feature preservation, save-time migration, board-profile validation, shared RoboStudio/deployment semantics, capability-only header generation and shipped V2 defaults;
- existing B2.3 hardware runtime-path regression now also verifies legacy packaged V1 defaults migrate correctly and first user save persists V2;
- existing RoboStudio hardware-config and macro-generator unit tests are retained;
- dedicated CI: `.github/workflows/v2-hardware-config-migration.yml`.

Software verification evidence:

- implementation commit: `4cb701e5293ed5bfafef824b7361be3b206a76de`;
- BoardProfile/schema regression alignment: `4e4144666b9bd966e0baf517d6d9a6e349e86633`;
- CI runner/import-path corrections: `cc0121c6a48d9a5195bfead4203f0ded8cb224a9`, `b3fb1bf3d86b337a1025fe64e074c1ced3663b9e`;
- GitHub Actions `V2 HardwareConfig Migration` run `37419006668`: **PASS**;
- GitHub Actions `V2 BoardProfile Contract` run `37418795703`: **PASS**;
- focused V2 migration regression verifies V1->V2 feature preservation, no silent rewrite on load, explicit-save migration, unknown/missing profile rejection, shared RoboStudio/deployment semantics and capability-only header generation;
- B2.3 runtime-path regression verifies both source and packaged flows, including a legacy packaged V1 default migrating deterministically to V2;
- existing HardwareConfig unittest regression remains green under the canonical import layout.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `IMPLEMENTED`

### Dependencies

V2-SW-001.

---

## V2-RS-001 — RoboStudio Board Profile Awareness

**Priority:** P1  
**Status:** IMPLEMENTED

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

### Implementation / verification record

Implemented board-profile awareness:

- RoboStudio shared hardware metadata defines:
  - profile ID: `antech_robot_v2`;
  - display name: `AnTech Robot V2`;
  - revision: `v2`.
- metadata is validated against the frozen firmware `BoardProfile::ID` and `BoardProfile::REVISION`.
- both standard and responsive Hardware Configuration tabs show a dedicated read-only Board Profile section:
  - `Board: AnTech Robot V2`;
  - `Revision: v2`;
  - profile ID for diagnostics/support.
- UI copy explicitly states that students configure capabilities while physical pins/connectors are fixed by the board profile.
- unknown board profiles fail clearly through the shared board-profile definition contract.

Student capability boundary:

- selectable devices remain only the registered capability features:
  - Motor;
  - Motor Encoder;
  - Line Sensor;
  - Ultrasonic Sensor;
  - MPU6050 IMU;
  - Servo;
  - Buzzer.
- board infrastructure is not registered as student-selectable devices:
  - MCP23017;
  - Battery Monitor;
  - Motor Safety;
  - START;
  - Robot Health.
- Hardware tab uses capability checkboxes only; no GPIO/pin/address/connector editor is introduced.
- `hardware.json` still contains only schema/profile metadata plus capability flags and cannot remap physical wiring.

Software regression:

- `tests/v2_robostudio_board_profile/run_v2_robostudio_board_profile.py` verifies firmware/UI board metadata alignment, board/revision presentation in both Hardware tabs, infrastructure exclusion, no pin-remapping UI/config fields, and unknown-profile rejection;
- dedicated CI: `.github/workflows/v2-robostudio-board-profile.yml`;
- BoardProfile and HardwareConfig V2 regressions run in the same focused workflow.

Software verification evidence:

- implementation commit: `ccb3040eb60d20f89c4ea18956ca9738555808e4`;
- GitHub Actions `V2 RoboStudio Board Profile` run `37419587630`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37419587379`: **PASS**;
- GitHub Actions `V2 Robot Health Aggregate` run `37419587453`: **PASS**;
- focused regression verifies shared board metadata matches firmware `BoardProfile`, both Hardware-tab variants expose board identity/revision, infrastructure devices are not selectable, no GPIO/pin remapping controls exist, and unknown profiles fail clearly.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `IMPLEMENTED`

### Dependencies

V2-CONF-001.

---

## V2-RS-002 — Robot Health Panel

**Priority:** P2  
**Status:** IMPLEMENTED

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

### Implementation / verification record

Implemented RoboStudio health architecture:

- `RobotHealthClient` is a read-only HTTP client for `GET /api/v1/health`.
- network/transport failures raise `RobotHealthNetworkError`.
- reachable-but-malformed/incompatible health responses raise `RobotHealthPayloadError`.
- `RobotHealthPresenter` maps one validated endpoint snapshot into separate Student and Teacher views.
- `RobotHealthPanel` is shared by standard and responsive Robot tabs.
- health retrieval runs in a `QThread` worker so the UI is not blocked.
- selecting an online robot refreshes health automatically; a manual `Refresh Health` action remains available.

Student view:

- shows only:
  - `Robot Connected`;
  - `Battery <state>`;
  - `Motor SAFE/ARMED/FAULT`;
  - `Line Sensor OK/CHECK/N/A`.
- raw reset/RSSI/count/I2C details are not included in the Student presenter.
- Teacher Diagnostics is collapsed by default.

Teacher/Diagnostic view:

- battery voltage/state;
- reset reason;
- Wi-Fi RSSI;
- raw 5-bit Line5 mask;
- encoder availability/health and left/right counts;
- motor state/armed/enabled;
- firmware version;
- board revision;
- uptime;
- System I2C/MCP23017 health;
- last motor stop/disarm reason.

Health-source completion required by this task:

- V2-RS-002 requirement includes encoder count/status, while V2-NET-001 initially exposed only encoder availability/health.
- `RobotHealthEncoder` is therefore extended with read-only `leftCount/rightCount`.
- `RobotHealthInputsInternal` reads existing Encoder counters without adding a student/public RobotAPI.
- `/api/v1/health` now serializes `encoder.left_count/right_count`.
- all health consumers remain aggregate/endpoint based; RoboStudio does not call RobotAPI or hardware subsystems directly.

Network-vs-robot-fault semantics:

- an HTTP transport failure renders `Connection error` and clears subsystem summary values to unknown placeholders;
- it does not display Battery/Motor/Line as FAULT;
- malformed robot health data renders a separate `Health data error`;
- actual robot fault states are rendered only from a valid health payload.

Software regression:

- `tests/v2_robot_health_panel/run_v2_robot_health_panel.py` verifies Student simplicity, full Teacher diagnostics, network/payload error separation, collapsed Teacher details and shared async panel integration in both Robot tabs;
- RobotHealth aggregate and HTTP serializer regressions are executed in the same focused workflow;
- dedicated CI: `.github/workflows/v2-robostudio-health-panel.yml`.

Software verification evidence:

- implementation commit: `16846a2c3917ac639c3788bbdfc3e36aba7e14a1`;
- GitHub Actions `V2 RoboStudio Health Panel` run `37420210724`: **PASS**;
- GitHub Actions `V2 Robot Health Aggregate` run `37420210617`: **PASS**;
- GitHub Actions `V2 Health HTTP Contract` run `37420210461`: **PASS**;
- GitHub Actions `V2 Encoder Contract` run `37420210472`: **PASS**;
- focused regression verifies Student simplicity, complete Teacher diagnostics including encoder counts, async endpoint consumption, network/payload error separation, and shared panel integration in standard/responsive Robot tabs.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `IMPLEMENTED`

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
**Status:** PENDING_HW

Required cases:

```text
BOOT -> SAFE
motion before START -> blocked
START -> ARMED
OTA -> SAFE
critical battery -> safe physical state
fault -> safe physical state
reset -> SAFE
```

Hard requirement:

> No software path shall produce non-zero physical motor output while `armed == false`.

### Software acceptance contract

A dedicated integrated acceptance runner now executes the real C++ controllers together rather than relying only on separate unit/regression suites:

- `MotorSafetyController`;
- `StartArmController`;
- `BatteryMonitor`;
- `BatterySafetyPolicy`;
- `ResetReasonService`.

Verified software behavior:

- BOOT begins in `BOOT`, then `begin()` forces `SAFE` with physical gate disabled;
- non-zero motion before START is rejected;
- a valid debounced START edge transitions `SAFE -> ARMED`;
- armed motion may transition `ARMED -> RUNNING`;
- OTA disarm returns motor safety to `SAFE`, disables driver and blocks later non-zero output until a new START edge;
- critical battery intentionally transitions to `FAULT` with STBY disabled, which is the required physically-safe state;
- battery hysteresis recovery transitions the matching LOW_BATTERY `FAULT -> SAFE` without auto-arm;
- fatal platform fault remains `FAULT`, driver disabled, and cannot be direct-armed;
- watchdog/reset reboot context starts `SAFE`, driver disabled, and requires a fresh START;
- all physical motor `ledcWrite(MOTOR_*)` calls remain inside `_setMotorsRaw()`;
- `_setMotorsRaw()` evaluates `MotorSafetyController::allowPhysicalOutput()` before any non-zero PWM write;
- blocked requests actively write zero duty on all four motor inputs;
- OTA/reboot/fatal lifecycle sources route through the system fail-safe disarm boundary;
- public RobotAPI/VM do not expose arm ownership;
- `StartArmController` remains the only approved production caller of `MotorSafetyController::arm()`.

Clarification of the original shorthand acceptance wording:

- `critical battery -> SAFE` means **physically safe / motor driver disabled**; software state is deliberately `FAULT` while voltage remains CRITICAL, then becomes `SAFE` only after hysteretic recovery;
- `fault -> SAFE` means **physical output safe (STBY LOW / no non-zero drive)**; fatal faults remain logically `FAULT` until their defined recovery/reset policy.

Software evidence:

- integrated runner: `tests/v2_motor_safety_acceptance/run_v2_motor_safety_acceptance.py`;
- dedicated CI: `.github/workflows/v2-motor-safety-acceptance.yml`;
- component regressions remain mandatory in the same workflow.

Hardware acceptance still required:

- verify GPIO4/STBY is LOW during boot/reset/fault/OTA/critical battery on a physical V2 board;
- verify non-zero commands before START produce no motor movement;
- verify GPIO33 START debounce/held-at-boot behavior electrically;
- verify physical motor remains stopped through OTA failure/reboot and critical-battery events.

Software verification evidence:

- integrated acceptance implementation: `d615aabc123294cf907dd176c58f91774ccd7d06`;
- GitHub Actions `V2 Motor Safety Acceptance` run `37421146181`: **PASS**;
- GitHub Actions `V2 Motor Safety Contract` run `37421146124`: **PASS**;
- GitHub Actions `V2 START ARM Contract` run `37421145989`: **PASS**;
- GitHub Actions `V2 Fail Safe Disarm Contract` run `37421146154`: **PASS**;
- GitHub Actions `V2 Critical Battery Safety` run `37421146063`: **PASS**;
- GitHub Actions `V2 Reset Reason Contract` run `37421146088`: **PASS**;
- the integrated host C++ acceptance executes BOOT, START, OTA, CRITICAL battery, fatal fault and watchdog/reset semantics in one scenario and verifies the physical-output gate remains disabled whenever motion is not authorized.

**Verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

---

## V2-TEST-004 — Line5 Regression

**Priority:** P1  
**Status:** BLOCKED

Representative masks:

```text
00100
01100
11000
00011
00000
11111
```

Required test scope:

```text
perception
weighted error
recovery
intersection
station pattern
public API raw mask
```

### Integrated software acceptance

A dedicated Line5 acceptance runner now executes the real V2 acquisition and perception components together:

```text
MCP23017 Port-A physical bits
        ↓
LineSensorBank
        ↓
canonical FL/L/C/R/FR 5-bit mask
        ↓
LineErrorEstimator / LinePerception
        ↓
IntersectionDetector / RecoveryStrategy
        ↓
public Line5 raw/API contract
```

Verified software behavior:

- physical GPA0..GPA4 ordering converts to canonical `FL/L/C/R/FR` without leaking MCP pin order to public APIs;
- each `LineSensorBank::readMask()` performs exactly one Port-A read;
- representative masks are locked:
  - `00100` -> error 0.0 -> CENTER;
  - `01100` -> error -0.5 -> LEFT_CENTER;
  - `11000` -> error -1.5 -> LEFT;
  - `00011` -> error +1.5 -> RIGHT;
  - `00000` -> LOST;
  - `11111` -> INTERSECTION at perception level;
- high bits are sanitized to the canonical five-bit contract;
- current intersection temporal policy is locked as a six-sample history with 3..5 candidates producing detection after the window is full;
- the frozen baseline quirk that 6/6 candidate samples returns false is recorded, not silently changed;
- recovery follows the last meaningful direction;
- any non-zero mask preserves the frozen V1 immediate-reacquire behavior;
- public `GetTraceRaw()` performs one canonical LineSensorBank acquisition and does not fall back to SensorManager/direct GPIO;
- public Line5 signatures and channel compatibility remain covered by `V2-SW-005`;
- existing line-response timing markers remain available for `V2-TEST-005` hardware measurement.

### Station-pattern requirement gap

The required item `station pattern` cannot be honestly marked PASS:

- the frozen Line service contains no distinct `StationPattern` / `StationDetector` implementation;
- current `IntersectionDetector` only classifies masks with >=4 active eyes as intersection candidates and applies its temporal window;
- the source-of-truth does not define what distinguishes a delivery station from an intersection, which masks encode a station, persistence/timing rules, or false-positive policy;
- therefore intersection behavior must not be silently relabeled as station detection.

**Blocker:** `REQUIREMENT_GAP`

Closure requires an explicit product/algorithm requirement defining station semantics. If station detection is intended to be physically equivalent to intersection detection, that equivalence must be stated explicitly in source-of-truth before this test can close.

### Remaining hardware acceptance

- verify physical sensor active polarity;
- verify representative-mask perception on real Line5 hardware;
- verify recovery effectiveness/timing;
- verify intersection persistence and false-positive behavior;
- verify station behavior only after station semantics are defined;
- measure V2 MCP23017 line-response latency under `V2-TEST-005`.

Software verification evidence:

- integrated acceptance implementation: `7d117e79b73eb2bede9551a426f4d40260725b89`;
- test-harness correction only: `1ebfd881774eb26075c44f536ecc97718a037d1f`;
- GitHub Actions `V2 Line5 Acceptance` run `37422721154`: **PASS**;
- component regressions executed in the same workflow:
  - LineSensorBank: **PASS**;
  - Line API Compatibility: **PASS**;
  - Line Perception / Control: **PASS**;
- integrated host C++ acceptance verifies physical MCP Port-A mapping, canonical 5-bit masks, representative weighted error/perception, frozen intersection temporal behavior and recovery semantics;
- static acceptance verifies one-read public raw-mask acquisition, public Line5 API stability, explicit station requirement gap and preservation of line-response timing diagnostics.

**Verification status:** `VERIFIED_SW_PARTIAL`  
**Task status:** `BLOCKED` — `REQUIREMENT_GAP / PENDING_HW`

---

## V2-TEST-005 — Line Response Performance

**Priority:** P1  
**Status:** PENDING_HW

Preserve diagnostic measurements:

```text
sensor read
control
motor submit
total latency
```

Compare V1 direct GPIO vs V2 MCP23017.

Acceptance threshold shall be set only after the first physical hardware measurement.

### Software measurement contract

Existing `RobotAPI::LineBasis()` instrumentation is preserved:

- `sensorStartUs -> sensorDoneUs`: Line5 sensor acquisition;
- `sensorDoneUs -> controlDoneUs`: LineFollower control computation;
- `controlDoneUs -> outputDoneUs`: motor API/output submission;
- `sensorStartUs -> outputDoneUs`: total synchronous software response;
- `loop`: interval between consecutive LineBasis calls.

Instrumentation remains change-triggered on canonical 5-bit mask transitions to limit diagnostic logging overhead.

A reusable evidence tool is implemented:

- `tools/line_response_report.py`;
- parses real `[LINE-RESPONSE]` serial records;
- exports per-event CSV when requested;
- summarizes count/min/median/p95/max/mean for `loop_us`, `sensor_us`, `control_us`, `output_us`, and `total_us`;
- supports explicit labels such as `v1-direct-gpio` and `v2-mcp23017`;
- deliberately emits `acceptance_threshold=null` and `pass_fail=NOT_EVALUATED` until hardware evidence freezes a threshold.

Measurement procedure is documented in `robot-docs/motor-control/H23-D_LINE_RESPONSE_LATENCY_TRACE.md` and now refers to the canonical V2 5-bit Line5 mask rather than the obsolete 3-channel wording.

### Required physical comparison

Collect comparable serial traces from:

1. V1 direct-GPIO Line5 baseline;
2. V2 MCP23017 Line5 implementation.

Use equivalent track transitions/control conditions and retain:

- raw serial logs;
- parsed CSV files;
- statistical summaries;
- exact board/firmware revisions and test conditions.

After the first approved hardware measurement, source-of-truth must be updated with the selected acceptance metric(s) and threshold before this task can close.

Software verification evidence:

- implementation commit: `dfff396fbdf088b2ad1725c13991461079158a96`;
- GitHub Actions `V2 Line Response Performance` run `37423273192`: **PASS**;
- Line Perception regression executed in the same workflow: **PASS**;
- parser/report tool was executed against synthetic `[LINE-RESPONSE]` logs and verified field extraction, CSV export and count/min/median/p95/max/mean summaries;
- static contract verifies production instrumentation still measures sensor/control/output/total timestamps and remains controllable via `line diag on/off/status`;
- regression explicitly verifies no acceptance threshold or PASS/FAIL verdict is invented before hardware evidence.

**Software verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

---

## V2-TEST-006 — Servo Regression

**Priority:** P1  
**Status:** PENDING_HW

Required cases:

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

### Integrated software acceptance

A dedicated acceptance runner now executes the real `ServoHAL` with an injected PWM transport and verifies the complete software contract:

- Servo1 maps only through `BoardProfile::Pins::SERVO1 = GPIO16`;
- Servo2 maps only through `BoardProfile::Pins::SERVO2 = GPIO17`;
- both ports accept 0°, 90°, and 180°;
- values below 0° clamp to 0°;
- values above 180° clamp to 180°;
- duty is monotonic across 0° < 90° < 180°;
- repeated commands use lazy per-port PWM attach rather than reattaching on every write;
- invalid ports do not attach or write PWM and return `INVALID_PORT`;
- PWM attach/write failures return `PWM_ERROR`;
- feature OFF path returns before `ServoHAL::setAngle()` and cannot attach/write PWM;
- CRITICAL battery safety gate is evaluated before servo PWM submission and blocks new servo activity;
- public `RobotAPI::SetServo(port, angle)` signature remains unchanged;
- compiler emits `Opcode::SetServo`;
- VM dispatches `Opcode::SetServo -> RobotAPI::SetServo`;
- Servo HAL owns no motor pins and no MotorSafety/STBY path.

Current software PWM contract remains:

```text
frequency: 50 Hz
resolution: 16 bit
pulse range: 500..2500 us
angle range: 0..180 degrees
```

This task verifies consistency of that contract; it does not claim that 500/2500 µs are physically calibrated endpoints for every attached servo model.

Software evidence:

- component regression: `tests/v2_servo/run_v2_servo.py`;
- integrated acceptance: `tests/v2_servo_acceptance/run_v2_servo_acceptance.py`;
- dedicated CI: `.github/workflows/v2-servo-acceptance.yml`.

### Remaining hardware acceptance

- verify physical movement on Servo1/GPIO16;
- verify physical movement on Servo2/GPIO17;
- verify commanded 0°/90°/180° against the selected servo hardware;
- determine whether 500/2500 µs endpoints require calibration/limiting for the actual servo model;
- verify supply/load behavior and brownout risk under servo stall/start current;
- verify feature-OFF firmware produces no servo waveform on physical pins.

Software verification evidence:

- integrated acceptance implementation: `646cc3bec890731959af52ed3329db12ccb2b5ab`;
- GitHub Actions `V2 Servo Acceptance` run `37423933928`: **PASS**;
- component `V2 Servo HAL Contract` regression is included in the same acceptance workflow;
- host C++ acceptance verifies Servo1/Servo2, 0°/90°/180°, clamp behavior, invalid port isolation, lazy attach, PWM attach/write failures and current duty mapping;
- static/transport acceptance verifies feature-OFF no-drive behavior, CRITICAL-battery servo blocking, BoardProfile pin ownership, public RobotAPI stability, compiler opcode emission and VM dispatch;
- regression verifies Servo HAL does not own MotorSafety STBY or motor output pins.

**Verification status:** `VERIFIED_SW`  
**Task status:** `PENDING_HW`

---

## V2-TEST-007 — Health Schema Contract

**Priority:** P1  
**Status:** DONE

Verify `/api/v1/health`:

- old compatibility fields remain;
- new V2 fields exist;
- invalid optional devices do not corrupt JSON;
- no credentials/secrets exposed.

### Acceptance contract

A dedicated serializer/schema acceptance test compiles and executes the real `RobotHealthJsonSerializer` and parses the emitted JSON.

Compatibility-critical top-level fields are locked:

```text
status
ready
robot_ready
network_ready
ota
http_ota
hostname
ip
```

Mandatory V2 top-level fields are locked:

```text
uptime_ms
firmware_version
board_profile
board_revision
reset_reason
battery
motor
start
line
line_mask
encoder
i2c
i2c_ok
rssi
```

Nested object shapes are also locked:

- `battery { voltage, state }`;
- `motor { armed, enabled, state, last_stop_reason }`;
- `start { pressed, ready_for_press, armed_by_start_this_boot }`;
- `line { available, healthy, mask }`;
- `encoder { available, healthy, left_count, right_count }`;
- `i2c { healthy, mcp23017 }`.

### Degraded/optional-device contract

A degraded snapshot is serialized and parsed with:

- Battery state `INVALID`;
- Line unavailable/unhealthy;
- Encoder unavailable/unhealthy;
- I2C/MCP23017 unhealthy;
- empty IP / RSSI 0;
- Motor `FAULT`.

The degraded response must:

- remain valid JSON;
- preserve the exact same schema shape as a normal response;
- expose unavailable/invalid state explicitly rather than omit fields;
- remain accepted by the RoboStudio health schema validator.

### Consumer/schema strictness

RoboStudio health validation now requires the published compatibility/V2 identity fields including:

- `hostname`;
- `ip`;
- `ota`;
- `http_ota`;
- `board_profile`.

Missing required schema fields are rejected as `RobotHealthPayloadError`; the client does not invent defaults.

### Security / ownership

- `sendHealth()` consumes exactly one `RobotHealthService` snapshot and delegates serialization.
- HTTP layer does not recompute battery, motor, Line, MCP or I2C state.
- serializer/health endpoint expose no SSID, Wi-Fi password, OTA password, Authorization, Basic Auth or HTTP OTA credential data.
- JSON string escaping is exercised with quote, backslash, newline, tab and raw control characters.

Software evidence:

- existing component HTTP regression: `tests/v2_health_http/run_v2_health_http.py`;
- aggregate regression: `tests/v2_robot_health/run_v2_robot_health.py`;
- integrated schema acceptance: `tests/v2_health_schema_acceptance/run_v2_health_schema_acceptance.py`;
- dedicated CI: `.github/workflows/v2-health-schema-acceptance.yml`.

No physical hardware criterion is required for this schema/serialization contract. Hardware-dependent subsystem correctness remains owned by each subsystem task, but its health representation is verified here.

Software verification evidence:

- acceptance implementation: `9cb0179405d61b4647ef38fc76e81546fb576b62`;
- GitHub Actions `V2 Health Schema Acceptance` run `37427164927`: **PASS**;
- GitHub Actions `V2 Health HTTP Contract` run `37427164885`: **PASS**;
- normal and degraded snapshots both compile through the real C++ serializer and parse as JSON;
- schema-shape equality is verified between healthy and degraded optional-device states;
- RoboStudio validator accepts complete degraded health but rejects missing mandatory compatibility/V2 fields;
- endpoint ownership and secret-exclusion checks pass.
- schema hardening commits `5c8d9537ae36138944dbdcbfc0c0d79b07ceb8c4`, `a4cfa6b672de4efb773c117ec102366ccdecfe83`, and `887dd0ce98d370a1a699131e2ea5fb1e1261c50b` extend RoboStudio validation to `start`, `line_mask`, `i2c_ok`, alias consistency, every mandatory top-level/nested field, tab escaping and raw control-character escaping;
- GitHub Actions `V2 Health Schema Acceptance` run `37429914179`: **PASS** on `887dd0ce98d370a1a699131e2ea5fb1e1261c50b`.

**Verification status:** `VERIFIED_SW`  
**Task status:** `DONE`

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
**Status:** IMPLEMENTED

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

### Integrated software acceptance

Dedicated runner: `tests/v2_ota_safety_acceptance/run_v2_ota_safety_acceptance.py`.

The acceptance verifies:

- real `MotorSafetyController` + `StartArmController` execute the required ARMED -> RUNNING -> OTA disarm -> SAFE transition;
- OTA disarm disables the physical gate and blocks subsequent non-zero motor commands;
- a held START cannot undo OTA disarm;
- reboot creates a fresh MotorSafety instance in SAFE with the driver disabled;
- a START held through boot/readiness cannot auto-arm; a fresh release -> press sequence is required;
- ArduinoOTA `onOtaStart()` disarms before marking the update active;
- HTTP OTA upload-start disarms before `Update.begin(...)`;
- system disarm clears motor PWM/state before lowering STBY;
- while OTA is active, the main loop stops motion and returns before VM/behavior execution;
- successful HTTP OTA disarms with `REBOOT` before `ESP.restart()`;
- OTA error/abort/failure paths contain no arm operation;
- boot initializes MotorSafety SAFE before motor PWM channels are attached.

Regression dependencies executed in the same focused workflow:

- VM/student safety boundary;
- fail-safe disarm contract;
- integrated motor-safety acceptance.

Focused CI: `.github/workflows/v2-ota-safety-acceptance.yml`.

No separate hardware claim is made here until physical OTA/STBY behavior is exercised on V2 hardware; software contract closure is recorded independently from V2-TEST-003 physical motor-safety acceptance.

**Software verification status:** `IMPLEMENTED_PENDING_CI`  
**Task status:** `IMPLEMENTED`

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
| 4 | V2-SAFE-001 | MotorSafetyController — PENDING_HW | P0 | M2 |
| 5 | V2-SAFE-002 | START/ARM Button — PENDING_HW | P0 | M2 |
| 6 | V2-SAFE-003 | Fail-Safe Disarm Conditions — IN_PROGRESS | P0 | M2 |
| 7 | V2-SAFE-004 | VM / Student Code Safety Boundary — IMPLEMENTED | P0 | M2 |
| 8 | V2-SW-004 | LineSensorBank 5CH — PENDING_HW | P1 | M3 |
| 9 | V2-SW-005 | Line5 Public API Compatibility — DONE | P1 | M3 |
| 10 | V2-SW-006 | Line5 Perception / Control Upgrade — PENDING_HW | P1 | M3 |
| 11 | V2-SW-007 | Servo HAL — PENDING_HW | P1 | M3 |
| 12 | V2-SW-008 | MCP LED/Buzzer Migration — IN_PROGRESS | P1 | M3 |
| 13 | V2-SW-009 | Encoder V2 Board Integration — IN_PROGRESS | P1 | M3 |
| 14 | V2-HLT-001 | BatteryMonitor — PENDING_HW | P1 | M4 |
| 15 | V2-HLT-002 | Critical Battery Safety Policy — PENDING_HW | P1 | M4 |
| 16 | V2-HLT-003 | ResetReasonService — IMPLEMENTED | P1 | M4 |
| 17 | V2-HLT-004 | RobotHealth Aggregate — IN_PROGRESS | P1 | M4 |
| 18 | V2-NET-001 | Health API V2 — IMPLEMENTED | P1 | M4 |
| 19 | V2-HLT-005 | OLED Health Display — BLOCKED (hardware contract gap) | P2 | M4 |
| 20 | V2-CONF-001 | HardwareConfig V2 / Migration — IMPLEMENTED | P1 | M5 |
| 21 | V2-RS-001 | RoboStudio Board Awareness — IMPLEMENTED | P1 | M5 |
| 22 | V2-RS-002 | Robot Health Panel — IMPLEMENTED | P2 | M5 |
| 23 | V2-TEST-001 | Board Mapping Contract Tests — DONE | P0 | M6 |
| 24 | V2-TEST-002 | MCP23017 Unit/Mock Tests — IN_PROGRESS | P0/P1 | M6 |
| 25 | V2-TEST-003 | Motor Safety Contract Tests — PENDING_HW | P0 | M6 |
| 26 | V2-TEST-004 | Line5 Regression — BLOCKED (station requirement gap) | P1 | M6 |
| 27 | V2-TEST-005 | Line Response Performance — PENDING_HW | P1 | M6 |
| 28 | V2-TEST-006 | Servo Regression — PENDING_HW | P1 | M6 |
| 29 | V2-TEST-007 | Health Schema Contract — DONE | P1 | M6 |
| 30 | V2-TEST-008 | Hardware ON/OFF Matrix Extension | P1 | M6 |
| 31 | V2-TEST-009 | Config Migration Regression | P1 | M6 |
| 32 | V2-TEST-010 | OTA Safety Regression — IMPLEMENTED | P0 | M6 |

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
