# H35 — Compatibility / Upgrade Policy

## 1. Mục tiêu

H35 biến khái niệm “tương thích” thành một contract có thể kiểm tra bằng máy. Không thành phần nào được tự suy luận rằng hai phiên bản tương thích chỉ vì số phiên bản gần nhau, cùng major version, hoặc schema mới hơn.

Policy authoritative nằm tại:

`packages/robot-isa/compatibility_policy.json`

Evidence CI được tạo tại:

`.build/h35/compatibility-report.json`

## 2. Các trục version được quản lý

H35 quản lý đồng thời:

- Release version: `VERSION`.
- Robot Language version: `robot-language/specification/api.yaml`.
- Platform Contract generation: schema của canonical ISA, capability model và target profiles.
- Compiler compatibility generation.
- Firmware/VM compatibility generation.
- Robot discovery protocol và discovery schema.

Generation là contract version, không phải marketing version. `0.1.1` không tự động tương thích với `0.1.2`; chỉ compatibility matrix mới có quyền quyết định.

## 3. Baseline generation 1

Baseline H35 hiện tại:

- Release: `0.1.1`.
- Robot Language: `1.0.0`.
- Platform Contract generation: `1`.
- Compiler generation: `1`.
- Firmware generation: `1`.
- Discovery protocol: `antechkids.robot.v1`.
- Discovery schema: `1`.

Bốn SSoT có fingerprint được freeze:

- `robot-language/specification/api.yaml`
- `packages/robot-isa/canonical_isa.json`
- `packages/robot-isa/capability_model.json`
- `packages/robot-isa/target_profiles.json`

Nếu nội dung một SSoT thay đổi mà policy/generation không được cập nhật có chủ đích, H35 CI phải FAIL.

## 4. Compatibility matrix

### Generation 1 ↔ Generation 1

Compiler generation 1 + firmware generation 1 hỗ trợ:

- compile
- first-flash
- OTA
- run

Đây là normal supported pair.

### Legacy generation 0 → generation 1

Firmware trước H35 không có trường `compatibility_generation`. H35 không coi đây là wildcard; absence này được ánh xạ duy nhất thành **legacy generation 0**.

Generation 0 chỉ có migration path:

`firmware generation 0 --full firmware OTA--> firmware generation 1`

Nó không được khai báo là general runtime compatibility pair.

Mục đích là robot H34 đang tồn tại vẫn có thể được nâng cấp bằng RoboStudio H35 mà không biến mọi firmware không có metadata thành “tương thích”.

## 5. Fail-closed rules

- Unknown firmware generation: reject.
- Future generation: reject cho đến khi matrix được cập nhật.
- Forward compatibility: explicit only.
- Backward compatibility: explicit only.
- Downgrade: reject nếu không có entry rõ ràng.
- Contract change: phải review generation và compatibility policy.
- Schema change: phải có migration adapter/path rõ ràng.
- Semantic version (`x.y.z`) không bao giờ tự chứng minh compatibility.

## 6. Runtime enforcement

Firmware generation 1 quảng bá trong `/api/v1/info`:

```json
{
  "protocol": "antechkids.robot.v1",
  "schema_version": 1,
  "compatibility_generation": 1
}
```

RoboStudio discovery thực hiện:

- Field không tồn tại → legacy generation 0.
- `0` → legacy migration source đã biết.
- `1` → current firmware.
- giá trị khác → reject fail-closed.
- kiểu dữ liệu sai, số âm, boolean/string → reject.

Runtime constants trong `robostudio/domain/compatibility.py` là projection phục vụ frozen application. H35 CI bắt buộc projection này phải đồng bộ với authoritative JSON policy.

## 7. Upgrade procedure cho generation mới

Khi cần thay đổi API/ISA/capability/target semantics:

1. Xác định thay đổi có ảnh hưởng wire/runtime contract hay không.
2. Tăng compatibility generation khi contract cũ không còn tương đương.
3. Cập nhật fingerprints của SSoT.
4. Thêm pair mới vào `supported_pairs`; không sửa pair cũ thành wildcard.
5. Nếu phải hỗ trợ robot cũ, thêm migration entry cụ thể.
6. Cập nhật firmware advertised generation.
7. Cập nhật RoboStudio runtime projection.
8. Thêm regression positive cho pair mới và negative cho pair không hỗ trợ.
9. Chạy H32 → H33 → H34 → H35 trước production packaging.

Nếu không có migration implementation, policy phải ghi nhận incompatibility và reject thay vì silent downgrade.

## 8. Release gate

H35 gate phải chạy sau H34 và trước production ZIP:

`H32 → H33 → H34 → H35 → H26-A/H26-B → Production ZIP`

H35 FAIL khi có một trong các trường hợp:

- `VERSION` drift khỏi release được policy quản lý.
- Robot Language version drift.
- contract schema drift.
- fingerprint API/ISA/capability/target drift.
- compiler/firmware projection drift.
- firmware discovery generation drift.
- current compiler/firmware pair không được allow-list.
- legacy migration path biến mất.
- future/unknown generation bị accept ngầm.

## 9. Definition of Done

H35 hoàn tất khi:

- Có một authoritative compatibility policy.
- Current compiler/firmware pair được explicit allow-list.
- Legacy H34 robot có migration path một chiều rõ ràng.
- Unknown/future generation fail-closed.
- Firmware công bố compatibility generation.
- RoboStudio phân loại generation khi discovery.
- Contract fingerprints bảo vệ silent semantic drift.
- Machine-readable evidence được sinh ra.
- Dedicated H35 CI gate chạy trước packaging.
- H32/H33/H34 và full regression không bị phá.

## 10. VM-RT closure review (#313)

Final compatibility classification for the VM Real-Time Control Responsiveness initiative is **NO GENERATION CHANGE REQUIRED**.

The cooperative scheduler, pending/resume state, shared line snapshot, timing telemetry and firmware-loop integration change runtime scheduling and boundedness, but do not change canonical opcode numbering, bytecode encoding, Robot Language API, platform contract schema, compiler generation, firmware generation or discovery protocol/schema. Legacy direct `Step()` semantics remain covered by regression gates and the current generation-1 compiler/firmware pair remains explicitly supported.

Therefore the authoritative compatibility policy remains at generation 1. A generation bump must not be introduced solely because responsiveness scheduling changed internally.

Physical timing qualification is tracked separately in #325. Timing thresholds and slice-budget tuning are operational qualification evidence; they are not, by themselves, a reason to change H35 compatibility generation unless the resulting implementation changes an externally observable contract covered by this policy.
