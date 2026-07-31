# Sprint S3.0 --- RoboSim API Contract & Capability Inventory

**Assignee:** DeepSeek\
**Epic:** RoboSim Compatibility\
**Milestone:** RC1 --- RoboSim Line Robot Compatibility\
**Priority:** Critical\
**Type:** Analysis / Contract Definition

## Background

Robot Platform đã có Compiler, VM, RobotAPI, Motor control, Sensor
Framework và HAL prototype, nhưng mức hỗ trợ RoboSim API vẫn thấp.
Sprint này tạo contract chính thức cho nhóm API của RC1 trước khi
implementation.

## RC1 Acceptance Program

``` python
import rcu
import _thread

def task1():
  while True:
    if (rcu.GetLightSensorData(1) == 1):
      rcu.SetMoveSpeed(-50, -50)
      rcu.line_intersection_stop(70, 17)
    else:
      rcu.SetMoveRunSecond("turnright", 50, 0.5)
      rcu.SetMoveRunSecond("forward", 50, 5)
      if (rcu.GetTraceV2I2CState(1, 1)):
        rcu.line_turn_encounterline(70, 20, 1)
      if (rcu.GetTraceV2I2C(1, 1) == 50):
        rcu.line_basis(70)
      if (rcu.GetTraceV2I2CChxState(1, 1)):
        rcu.line_set_initialize(1, "black", "wheeledchassis")
        rcu.line_intersection_stop(70, 17)
        rcu.line_for_bmp(70, 360)

def task2():
  while True:
    if (rcu.GetLightSensorData(1)):
      rcu.SetMoveSpeed(50, 50)
    if (rcu.GetLightSensor(1) == 50):
      rcu.SetMoveRunAngle("forward", 50, 50)

_thread.start_new_thread(task1,())
_thread.start_new_thread(task2,())

while 1:
  pass
```

## Hardware Constraint

Robot v1 dùng TCRT5000/Tracker 3 mắt, chỉ có digital L/C/R.

Chiến lược: - Light Sensor digital: dùng từng channel riêng. - Patrol:
gom 3 channel thành array 3 mắt. - Không fake analog/raw. - Không fake 8
channel thành FULL compatibility.

## APIs to Inventory

### Light

-   `GetLightSensorData()`
-   `GetLightSensor()`

### Patrol

-   `GetTraceV2I2CState()`
-   `GetTraceV2I2C()`
-   `GetTraceV2I2CChxState()`

### Motion

-   `SetMoveSpeed()`
-   `SetMoveRunSecond()`
-   `SetMoveRunAngle()`

### Line Behavior

-   `line_set_initialize()`
-   `line_basis()`
-   `line_intersection_stop()`
-   `line_turn_encounterline()`
-   `line_for_bmp()`

### Runtime / Language

-   `_thread.start_new_thread()`
-   `while True`
-   `while 1`
-   `global`
-   function calls
-   nested `if`
-   multiple concurrent infinite tasks

## Required Analysis Per API

Mỗi API phải xác định:

1.  Signature: parameters, types, return type, valid ranges,
    blocking/non-blocking.
2.  Semantic meaning.
3.  Category: `HARDWARE_PRIMITIVE`, `ACTUATOR_PRIMITIVE`, `BEHAVIOR`,
    `RUNTIME`, `LANGUAGE_FEATURE`.
4.  Current support ở Adapter → Compiler → Bytecode → VM → RobotAPI →
    Framework → Driver → HAL → Hardware.
5.  Physical mapping.
6.  Compatibility: `FULL`, `ADAPTED`, `UNSUPPORTED`, `UNKNOWN`.

Không đoán semantics. Nếu thiếu evidence, ghi `UNKNOWN`.

## Special Investigation --- Light Sensor

Xác minh chính xác khác biệt giữa `GetLightSensorData()` và
`GetLightSensor()`.

Nếu `GetLightSensor()` là analog/raw thì Robot v1 phải ghi
`UNSUPPORTED`; không chuyển digital 0/1 giả thành 0..100.

## Special Investigation --- Patrol Card

Reverse-engineer: - semantics của ba API Trace, - cách biểu diễn 8
mắt, - port/channel numbering, - black/white convention, -
`GetTraceV2I2C()` trả raw, position, percentage hay kiểu khác.

Sau đó mới đánh giá mapping xuống L/C/R.

## Special Investigation --- line\_\* APIs

Xem các API `line_*` là candidate `BEHAVIOR`.

Xác định cho từng API: - ý nghĩa parameter, - blocking behavior, -
termination condition, - motor dependency, - Patrol dependency, -
encoder dependency, - control/PID dependency.

Không biết thì giữ `UNKNOWN`.

## Runtime / \_thread Gap Analysis

Phân tích `task1`, `task2`, `main` và yêu cầu VM cho: - multiple
execution contexts, - independent PC/context, - infinite loops, -
cooperative scheduling candidate, - blocking RobotAPI calls, - wait
interaction, - shared globals, - race conditions.

Không implement scheduler trong Sprint này.

## Capability Matrix

Tạo bảng:

  --------------------------------------------------------------------------------------------------------------
  RoboSim   Category   Semantics   Adapter   Compiler   VM      RobotAPI   Firmware   Hardware   Compatibility
  API                  Known                                                                     
  --------- ---------- ----------- --------- ---------- ------- ---------- ---------- ---------- ---------------

  --------------------------------------------------------------------------------------------------------------

## End-to-End Mapping

Với API đã hiểu rõ, mô tả:

``` text
RoboSim
↓
Generated Python
↓
Adapter
↓
Compiler IR / Opcode
↓
VM
↓
RobotAPI / Behavior API
↓
Framework / Service
↓
HAL
↓
Hardware
```

## Architecture Classification

Định hướng:

``` text
Hardware Primitive
↓
RobotAPI
↓
Sensor/Motor Framework

Behavior
↓
Behavior API
↓
LineControlService
↙             ↘
Patrol Adapter   Motion
```

Không đặt `line_*` algorithm vào Sensor Framework.

## Deliverables

Tạo:

``` text
docs/robosim/
├── ROBOSIM_API_CAPABILITY_MATRIX.md
├── ROBOSIM_RC1_API_CONTRACT.md
├── ROBOSIM_RC1_RUNTIME_GAP_ANALYSIS.md
└── ROBOSIM_RC1_IMPLEMENTATION_PLAN.md
```

Implementation plan phải đề xuất S3.1--S3.5 dựa trên evidence, không dựa
trên giả định.

## Evidence Requirement

Ưu tiên evidence: 1. RoboSim generated code thực tế. 2. Existing
source/spec. 3. Existing adapter mappings. 4. Tests/examples. 5. Runtime
observations.

Nếu suy luận, ghi: - `Evidence: INFERRED` -
`Confidence: LOW/MEDIUM/HIGH`

## Acceptance Criteria

-   [ ] Inventory đầy đủ API của RC1 acceptance program.
-   [ ] Mỗi API có category và compatibility status.
-   [ ] Có platform gap analysis theo từng layer.
-   [ ] `line_*` có semantics hoặc được đánh dấu UNKNOWN.
-   [ ] Không fake analog cho TCRT5000 digital.
-   [ ] Mô tả rõ giới hạn Patrol 8-eye → 3-eye.
-   [ ] Phân tích `_thread` runtime gap.
-   [ ] Có end-to-end mapping.
-   [ ] Có implementation plan dựa trên evidence.
-   [ ] Không broad implementation ngoài scope.

## Non-Goals

-   Không implement toàn bộ RoboSim API.
-   Không viết Line PID.
-   Không viết VM scheduler.
-   Không fake analog sensor.
-   Không fake 8-eye hardware.
-   Không refactor HAL.
-   Không thêm sensor mới.

## Review Gate

Không bắt đầu S3.1 tự động.

Sau khi hoàn thành, gửi toàn bộ deliverables để Architecture Review. Chỉ
freeze RC1 contract và bắt đầu implementation sau khi review được chấp
nhận.

## Definition of Success

Sprint thành công khi có thể trả lời chính xác:

> Với từng API trong chương trình RoboSim RC1, command/data đi qua những
> layer nào, platform hiện thiếu gì, hardware thật đáp ứng đến mức nào,
> và cần implement gì để chương trình cuối cùng chạy đúng trên robot
> thật?
