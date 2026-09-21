# EPIC H32 — Platform Contract Consolidation

## 1. Mục tiêu

H32 loại bỏ tình trạng các lớp trong hệ thống có thể tự hiểu khác nhau về cùng một operation.

Trước H32, repository đã có các contract canonical tốt, nhưng chúng nằm ở các boundary khác nhau:

- public/source API;
- canonical ISA / wire opcode;
- capability model;
- target capability profile.

Các file này không sai, nhưng thiếu một gate duy nhất chứng minh rằng chúng vẫn mô tả cùng một platform contract.

H32 **không tạo một source of truth mới**. Thay vào đó, H32 định nghĩa rõ ownership, join các canonical source để validation, và tạo một projection chỉ dùng làm evidence.

---

## 2. Canonical ownership

| Concern | Canonical source | Ownership |
| --- | --- | --- |
| API name, arguments, return type, semantic metadata | `robot-language/specification/api.yaml` | Robot Language API |
| Canonical operation identity, producer name, numeric wire opcode, canonical order | `packages/robot-isa/canonical_isa.json` | ISA |
| Opcode → capability assignment | `packages/robot-isa/capability_model.json` | Capability model |
| Target → supported capabilities | `packages/robot-isa/target_profiles.json` | Target profiles |

Không layer nào được copy các dữ liệu trên thành một contract authoritative riêng.

Ví dụ:

```text
sensor.read_ultrasonic
        │
        ├── API name/signature      → api.yaml
        ├── ReadUltrasonic / 30     → canonical_isa.json
        ├── sensor.ultrasonic       → capability_model.json
        └── esp32/arduino/robosim   → target_profiles.json
```

---

## 3. Consolidated projection

`tools/platform_contract.py` join bốn canonical source thành một view deterministic.

Mặc định:

```text
artifacts/platform_contract.json
```

Projection này:

- là generated evidence;
- không được check-in như canonical package data;
- không được compiler/runtime/RoboStudio dùng làm production dependency;
- có thể dùng để review, debug contract, CI evidence hoặc release audit.

Nếu production code bắt đầu đọc `platform_contract.json`, H32 regression phải fail.

---

## 4. Invariants

H32 fail-closed nếu một trong các invariant sau bị phá:

1. Mỗi `api.yaml` opcode producer name phải tồn tại đúng một lần trong canonical ISA.
2. Mỗi canonical ISA producer name phải có đúng một API entry.
3. `api.yaml.opcode_id` phải bằng `canonical_isa.numeric_code`.
4. Canonical semantic ID, producer name, wire code và canonical index phải unique.
5. `canonical_index` phải contiguous theo canonical row order.
6. Mỗi canonical opcode phải thuộc đúng một capability.
7. Capability không được tham chiếu opcode không tồn tại.
8. Target profile không được tham chiếu capability không tồn tại.
9. Mọi target phải có tất cả capability được đánh dấu `required=true`.
10. Generated platform projection không được trở thành production source of truth.

---

## 5. Quy trình thay đổi contract

### 5.1 Thêm hoặc đổi public API

Sửa owner của API semantics:

```text
robot-language/specification/api.yaml
```

Nếu operation mới cần opcode mới, đồng thời cập nhật:

```text
packages/robot-isa/canonical_isa.json
packages/robot-isa/capability_model.json
```

và target support nếu cần:

```text
packages/robot-isa/target_profiles.json
```

Sau đó chạy H32 gate.

### 5.2 Đổi numeric opcode

Numeric wire opcode thuộc ISA, vì vậy bắt đầu từ:

```text
packages/robot-isa/canonical_isa.json
```

Sau đó cập nhật API `opcode_id` và capability opcode reference tương ứng.

H32 sẽ reject trạng thái trung gian bị lệch.

### 5.3 Đổi capability ownership

Sửa:

```text
packages/robot-isa/capability_model.json
```

Mỗi opcode chỉ được có một owner capability.

### 5.4 Đổi target support

Sửa:

```text
packages/robot-isa/target_profiles.json
```

Không hardcode target support trong compiler/UI riêng lẻ nếu dữ liệu đó đã thuộc target profile.

---

## 6. Current contract snapshot

Tại thời điểm H32:

- 60 canonical opcodes;
- 38 public/platform operations;
- 22 internal VM operations;
- 16 capabilities;
- 3 targets: `robosim`, `esp32`, `arduino`;
- required capabilities: `motion.basic`, `runtime.control`.

Một số khác biệt target được cố ý giữ:

- `motion.encoder_angle` chỉ hỗ trợ `robosim`;
- `peripheral.lizard` hỗ trợ `robosim` và `esp32`, không hỗ trợ `arduino`.

H32 không thay đổi các policy này; H32 chỉ làm chúng có thể kiểm chứng cross-layer.

---

## 7. CI contract

Dedicated gate:

```text
tests/h32_platform_contract/run_h32_platform_contract.py
```

Gate chạy trước full Windows production ZIP build để contract drift fail sớm.

Gate cũng sinh:

```text
artifacts/platform_contract.json
```

Existing Actions artifact upload sẽ giữ file này trong `robotics-test-artifacts` để review.

Full `run_all_tests.py` chạy lại H32 để tránh dedicated CI step và repository regression diverge.

---

## 8. Scope boundary

H32 không:

- thay numeric opcode hiện tại;
- thêm/remove API;
- thay semantics của RobotAPI;
- thay capability support hiện tại;
- thay VM execution behavior;
- thay RoboSim adapter semantics.

H32 là architecture/contract consolidation + validation layer.

---

## 9. Acceptance

H32 hoàn tất khi:

- dedicated H32 gate PASS;
- architecture migration gate vẫn PASS;
- full Windows production ZIP PASS;
- `RoboStudio-Production-Windows` upload PASS;
- full repository regression PASS;
- generated platform contract evidence được upload;
- không có production consumer của generated projection.
