# EPIC H33 — Capability–Compiler Binding

## 1. Mục tiêu

H33 biến contract đã consolidate ở H32 thành luật được compiler enforce trước khi emit chương trình.

Chuỗi bắt buộc:

```text
Source
  → Standard Robot API
  → Target profile
  → Capability validation
  → Resource validation
  → IR / bytecode / header
```

Một chương trình không tương thích target phải fail trước khi tạo output.

---

## 2. Canonical ownership

H33 không dùng `artifacts/platform_contract.json` làm production dependency.

Compiler đọc trực tiếp canonical owners của H32:

| Concern | Canonical source |
| --- | --- |
| Opcode identity | `packages/robot-isa/canonical_isa.json` |
| Opcode → capability | `packages/robot-isa/capability_model.json` |
| Target capabilities + resource constraints | `packages/robot-isa/target_profiles.json` |
| API → producer opcode | generated `FUNCTION_REGISTRY`, sinh từ `robot-language/specification/api.yaml` |

Production ZIP stage ba JSON canonical vào `compiler/contracts/`; đây là runtime copy của canonical source, không phải checked-in authority thứ hai.

---

## 3. Compile target

`RobotCompiler` nhận target:

```python
RobotCompiler(target="esp32")
```

Default của generic compiler là `robosim` để giữ backward compatibility.

Các physical build boundary truyền `esp32` rõ ràng.

RoboStudio compiler contract nhận:

```json
{
  "target": "esp32"
}
```

và mặc định `esp32`.

Unknown target:

```text
E_TARGET_UNKNOWN
```

---

## 4. Capability enforcement

Mỗi built-in Robot API đã có producer opcode trong `FUNCTION_REGISTRY`.

H33 resolve:

```text
API
 → producer name
 → canonical numeric opcode
 → capability owner
 → target capability set
```

Validation chạy trước handler.

Ví dụ:

```text
set_move_initialize
 → MoveInitialize
 → 52
 → motion.encoder_angle
```

`robosim` hỗ trợ capability trên, `esp32` không hỗ trợ.

ESP32 compile fail:

```text
E_CAPABILITY_MISSING
```

---

## 5. Resource contract

H33 thêm optional `resources[]` vào canonical `target_profiles.json`.

Resource đầu tiên:

```text
sensor.line.channel
```

Bindings:

```text
read_line        argument 0
get_trace_value  argument 1
get_trace_state  argument 1
```

Bounds:

```text
robosim : 0..6
esp32   : 0..2
arduino : 0..2
```

RoboSim frontend chỉ normalize representation:

```text
RoboSim 1..7 → canonical 0..6
```

Frontend không quyết định physical availability.

Compiler target contract mới là owner của quyết định target compatibility.

---

## 6. Static / dynamic resource policy

Literal resource:

```python
read_line(2)
```

được validate compile-time.

Out of range:

```text
E_RESOURCE_OUT_OF_RANGE
```

Dynamic resource:

```python
channel = x
read_line(channel)
```

hiện fail-closed:

```text
E_DYNAMIC_RESOURCE_UNSAFE
```

Lý do: runtime hiện chưa có contract chứng minh bounds-check an toàn cho constrained resource.

Sau này chỉ đổi policy sang `runtime` khi runtime validation đã có regression proof.

---

## 7. Structured diagnostic

`CompilerError` giữ backward-compatible message và thêm:

```text
code
severity
message
context
```

Context có thể chứa:

```text
api
target
capability
opcode
resource
resource_min
resource_max
line
column
```

RoboStudio bridge trả lại cùng error code và diagnostic của compiler, không tự suy luận capability rule.

---

## 8. RoboSim adapter

Trước H33, trace normalizer gắn cứng real robot 3 channel.

Sau H33:

```text
RoboSim source
   ↓
normalize 1..7 → 0..6
   ↓
Standard Robot API
   ↓
Compiler target validation
```

Ví dụ:

```text
GetTraceV2I2CState(1, 4)
    ↓
get_trace_state(1, 3)
```

- target `robosim`: PASS
- target `esp32`: `E_RESOURCE_OUT_OF_RANGE`

---

## 9. Production distribution

Production staging copy:

```text
packages/robot-isa/canonical_isa.json
packages/robot-isa/capability_model.json
packages/robot-isa/target_profiles.json
```

sang:

```text
compiler/contracts/
```

`target_contract.py` resolve hai layout:

```text
source checkout → packages/robot-isa/
production ZIP  → compiler/contracts/
```

Không dùng H32 generated projection.

---

## 10. Error codes

H33 enforce tối thiểu:

```text
E_TARGET_UNKNOWN
E_TARGET_PROFILE_INVALID
E_API_UNSUPPORTED
E_CAPABILITY_MISSING
E_RESOURCE_OUT_OF_RANGE
E_DYNAMIC_RESOURCE_UNSAFE
```

---

## 11. Regression gate

Dedicated gate:

```text
python tests/h33_capability_compiler/run_h33_capability_compiler.py
```

Coverage:

- supported API / target;
- unknown target;
- missing capability;
- API producer không canonical;
- static resource valid;
- static resource out of range;
- dynamic constrained resource;
- RoboSim channel normalization;
- RoboSim → ESP32 invalid channel;
- RoboSim full 7-channel target;
- RoboStudio bridge structured error;
- malformed target profile fail-closed;
- production contract staging;
- H32 generated projection không trở thành compiler dependency.

Gate cũng được thêm vào:

```text
run_all_tests.py
.github/workflows/robotics-ci.yml
```

---

## 12. Acceptance

H33 hoàn tất khi:

- target context đi vào compiler;
- capability validation chạy trước handler emit;
- resource validation chạy trước output generation;
- RoboSim frontend không còn hard-code ESP32 channel count;
- bridge trả structured compiler diagnostic;
- production ZIP mang canonical runtime contracts;
- H32 gate vẫn PASS;
- H33 dedicated gate PASS;
- full production ZIP build PASS;
- full repository regression PASS.
