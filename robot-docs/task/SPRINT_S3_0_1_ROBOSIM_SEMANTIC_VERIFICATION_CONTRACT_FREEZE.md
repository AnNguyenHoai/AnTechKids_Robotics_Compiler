# Sprint S3.0.1 --- RoboSim Semantic Verification & RC1 Contract Freeze

**Assignee:** DeepSeek\
**Epic:** RoboSim Compatibility\
**Milestone:** RC1 --- RoboSim Line Robot Compatibility\
**Priority:** Critical\
**Type:** Semantic Verification / Contract Definition\
**Prerequisite:** S3.0 Review Completed\
**Implementation Scope:** No feature implementation

------------------------------------------------------------------------

# 1. Background

Sprint S3.0 đã hoàn thành phần lớn codebase inventory, pipeline analysis
và runtime gap analysis.

Architecture Review xác nhận các phần sau có thể giữ nguyên:

-   Existing pipeline inventory
-   API classification
-   Hardware capability analysis
-   Compiler/VM gap analysis
-   `_thread` runtime gap analysis

Tuy nhiên RC1 API Contract **chưa thể freeze** vì một số RoboSim API vẫn
đang dựa trên suy luận thay vì evidence.

Không được bắt đầu S3.1 implementation cho đến khi Sprint S3.0.1 hoàn
thành và contract được review.

------------------------------------------------------------------------

# 2. Goal

Xác minh semantics thực tế của các RoboSim API còn `UNKNOWN` hoặc
`PARTIAL`, sau đó tạo:

``` text
ROBOSIM_RC1_API_CONTRACT v1.0
```

Contract phải đủ chính xác để Compiler, VM và Firmware có thể implement
mà không phải tự đoán behavior.

------------------------------------------------------------------------

# 3. APIs Requiring Verification

## Light Sensor

``` text
GetLightSensorData(port)
GetLightSensor(port)
```

Phải xác minh chính xác:

-   Return type
-   Return range
-   Digital hay analog/raw
-   Black/white convention
-   Ý nghĩa của `port`
-   Blocking/non-blocking

Không được suy luận rằng:

``` text
GetLightSensorData = digital
GetLightSensor = analog
```

nếu chưa có evidence.

------------------------------------------------------------------------

## Patrol Card

``` text
GetTraceV2I2CState(port, ...)
GetTraceV2I2C(port, ...)
GetTraceV2I2CChxState(port, channel)
```

Phải xác minh:

-   Ý nghĩa từng parameter
-   Return type/range
-   8 channel representation
-   Channel numbering
-   `State` semantics
-   `ChxState` semantics
-   `GetTraceV2I2C()` trả raw, position, percentage, mask hay dữ liệu
    khác
-   Black/white convention

Đây là **Critical Blocker** của RC1.

------------------------------------------------------------------------

## Line Behaviors

``` text
line_set_initialize()
line_basis()
line_intersection_stop()
line_turn_encounterline()
line_for_bmp()
```

Phải xác minh cho từng API:

-   Parameter semantics
-   Blocking hay non-blocking
-   Termination condition
-   Có điều khiển motor bên trong hay không
-   Có đọc Patrol Card bên trong hay không
-   Có dùng encoder không
-   Có PID/control loop không
-   Expected physical behavior

Không được implement placeholder/no-op.

------------------------------------------------------------------------

## Motion

``` text
SetMoveRunAngle(direction, speed, angle)
```

Phải xác minh:

-   `angle` là wheel rotation, chassis rotation hay encoder target
-   Unit
-   Blocking behavior
-   Điều kiện kết thúc
-   Có feedback/encoder dependency không

Không được tự động convert:

``` text
angle → delay time
```

trừ khi contract chứng minh đó là semantics RoboSim.

------------------------------------------------------------------------

# 4. Evidence Strategy

DeepSeek phải tìm evidence theo thứ tự ưu tiên:

1.  RoboSim generated Python từ các block khác nhau.
2.  Các sample RoboSim hiện có trong repository.
3.  Existing RoboSim API specs/docs trong codebase.
4.  Existing adapter mappings/tests.
5.  Runtime experiments trên RoboSim.
6.  Controlled experiments bằng cách thay parameter và quan sát
    generated code/behavior.

Nếu vẫn không xác định được:

``` text
Semantic Status: UNKNOWN
Evidence: INSUFFICIENT
```

Không được biến suy luận thành contract.

------------------------------------------------------------------------

# 5. Controlled Experiment Requirement

Với API chưa rõ parameter, tạo các chương trình RoboSim tối thiểu để
isolate API.

Ví dụ concept:

``` text
Experiment A
parameter = 1

Experiment B
parameter = 2

Experiment C
parameter = 50
```

So sánh:

-   Generated Python
-   Simulation behavior
-   Return value nếu quan sát được

Mỗi experiment phải ghi:

``` text
Input
Generated Code
Observed Behavior
Conclusion
Confidence
```

------------------------------------------------------------------------

# 6. Light Sensor Hardware Constraint

Hardware Robot v1 hiện tại:

``` text
TCRT5000 3-eye

LEFT    CENTER    RIGHT
  │        │        │
digital  digital  digital
```

Không có analog output.

Sau khi semantics được xác minh:

-   Nếu RoboSim API chỉ yêu cầu digital → có thể `FULL`.
-   Nếu yêu cầu analog/raw → `UNSUPPORTED` trên Robot v1.
-   Nếu có thể giữ behavior nhưng giảm fidelity → `ADAPTED`.

Không fake analog:

``` text
0 → 0
1 → 100
```

trừ khi đó chính là contract của RoboSim.

------------------------------------------------------------------------

# 7. Patrol Hardware Constraint

RoboSim Patrol Card có 8 mắt nhưng Robot v1 hiện có:

``` text
L C R
```

Sau khi xác minh semantics, đánh giá từng API độc lập.

Không được mặc định:

``` text
8-eye RoboSim == 3-eye Robot v1
```

Có thể kết luận:

``` text
FULL
ADAPTED
UNSUPPORTED
```

khác nhau cho từng Patrol API.

------------------------------------------------------------------------

# 8. Compatibility Must Be Layered

Không dùng một trạng thái duy nhất để che giấu pipeline.

Ví dụ:

``` text
GetLightSensor()

Adapter        FULL
Compiler       FULL
VM             FULL
RobotAPI       FULL
Hardware       UNSUPPORTED
Overall        UNSUPPORTED
```

Capability Matrix phải phân biệt:

``` text
Software Support
Physical Support
Overall Compatibility
```

------------------------------------------------------------------------

# 9. Forbidden Implementation Assumptions

Không được đưa các assumption sau vào implementation plan nếu chưa có
evidence:

``` text
line_set_initialize() → no-op
line_for_bmp() → no-op
line_intersection_stop(type) → ignore type
SetMoveRunAngle(angle) → angle × delay calibration
GetLightSensor digital → fake analog
8 Patrol channels → silently map to 3 channels
```

Nếu cần approximation trong tương lai, contract phải đánh dấu rõ:

``` text
ADAPTED / APPROXIMATED
```

và Architecture Review phải approve trước.

------------------------------------------------------------------------

# 10. Update Existing Deliverables

Không cần viết lại toàn bộ S3.0.

Cập nhật:

``` text
docs/robosim/
├── ROBOSIM_API_CAPABILITY_MATRIX.md
├── ROBOSIM_RC1_API_CONTRACT.md
└── ROBOSIM_RC1_IMPLEMENTATION_PLAN.md
```

Giữ lại `ROBOSIM_RC1_RUNTIME_GAP_ANALYSIS.md` nếu không có evidence mới
làm thay đổi kết luận.

------------------------------------------------------------------------

# 11. New Deliverable

Tạo:

``` text
docs/robosim/ROBOSIM_RC1_SEMANTIC_EVIDENCE.md
```

Với mỗi API:

``` text
## API Name

Signature:
Category:

Evidence:
- ...

Experiments:
- ...

Observed behavior:
- ...

Conclusion:
- ...

Semantic Status:
KNOWN / PARTIAL / UNKNOWN

Confidence:
HIGH / MEDIUM / LOW
```

------------------------------------------------------------------------

# 12. Contract Freeze Rules

Một API chỉ được đưa vào `ROBOSIM_RC1_API_CONTRACT v1.0` với
implementation semantics cụ thể khi:

``` text
Semantic Status = KNOWN
```

và evidence đủ mạnh.

Nếu:

``` text
PARTIAL
UNKNOWN
```

contract phải giữ rõ limitation.

Không thiết kế opcode/RobotAPI behavior dựa trên phần semantics chưa
biết.

------------------------------------------------------------------------

# 13. Expected Output Classification

Sau sprint, mỗi API phải rơi vào một trong các trường hợp:

``` text
KNOWN + FULL
KNOWN + ADAPTED
KNOWN + UNSUPPORTED
PARTIAL
UNKNOWN
```

`UNKNOWN` được chấp nhận nếu thật sự không thể xác minh.

Điều quan trọng là **không đoán**.

------------------------------------------------------------------------

# 14. Acceptance Criteria

Sprint PASS khi:

-   [ ] Light Sensor semantics được xác minh hoặc giữ UNKNOWN có
    evidence.
-   [ ] Patrol API semantics được xác minh tối đa bằng controlled
    experiments.
-   [ ] `GetTraceV2I2C()` không còn bị đoán là raw/position/percentage
    nếu chưa có evidence.
-   [ ] Các `line_*` có evidence về parameter và behavior hoặc giữ
    UNKNOWN.
-   [ ] `SetMoveRunAngle()` semantics được xác minh.
-   [ ] Có `ROBOSIM_RC1_SEMANTIC_EVIDENCE.md`.
-   [ ] Capability Matrix tách Software / Hardware / Overall
    compatibility.
-   [ ] Không còn placeholder/no-op được đề xuất như implementation
    thật.
-   [ ] Không fake analog capability.
-   [ ] Không fake 8-eye capability.
-   [ ] `ROBOSIM_RC1_API_CONTRACT.md` đủ điều kiện đề xuất freeze v1.0.
-   [ ] Implementation Plan được cập nhật dựa trên verified semantics.

------------------------------------------------------------------------

# 15. Non-Goals

Không thực hiện:

-   Compiler feature implementation
-   New opcodes
-   VM scheduler
-   Line PID
-   Patrol Adapter implementation
-   Motor behavior implementation
-   HAL refactor
-   Hardware changes

Sprint này là **semantic verification only**.

------------------------------------------------------------------------

# 16. Review Gate

Sau khi hoàn thành:

``` text
S3.0.1
   ↓
Architecture Review
   ↓
Contract accepted?
   ├── NO → resolve blockers
   └── YES
         ↓
ROBOSIM_RC1_API_CONTRACT v1.0 FROZEN
         ↓
S3.1 Implementation
```

DeepSeek không tự bắt đầu S3.1.

------------------------------------------------------------------------

# Definition of Done

Sprint hoàn thành khi team có thể nhìn vào `ROBOSIM_RC1_API_CONTRACT.md`
và implement Compiler/VM/Firmware mà **không phải tự suy đoán ý nghĩa
của RoboSim API**.
