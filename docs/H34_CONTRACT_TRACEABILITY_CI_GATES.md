# H34 — Contract Traceability + CI Gates

## Mục tiêu

H34 biến các contract đã được chuẩn hóa ở H32/H33 thành một chuỗi traceability có thể kiểm tra tự động:

`Robot API → compiler registry → canonical opcode → capability → target profile → VM dispatch → runtime endpoint`

H34 không tạo thêm nguồn sự thật mới và không thêm tính năng robot. File JSON được sinh ra chỉ là evidence, không phải contract authority.

## Source of Truth

- Robot API: `robot-language/specification/api.yaml`
- Canonical ISA: `packages/robot-isa/canonical_isa.json`
- Capability model: `packages/robot-isa/capability_model.json`
- Target profiles/resources: `packages/robot-isa/target_profiles.json`

Implementation evidence:

- Compiler binding: `robot-compiler/compiler/generated/function_registry.py`
- Generated opcode enum: `robot-compiler/compiler/generated/opcode.py`
- Runtime dispatch: `robot-platform/main/src/Services/VM/VM.cpp`

## Traceability invariants

Mỗi public API phải thỏa tất cả điều kiện sau:

1. Có đúng một API definition trong `api.yaml`.
2. Opcode name và numeric ID khớp canonical ISA.
3. Có compiler binding trong generated function registry và binding dùng đúng opcode.
4. Generated Python Opcode enum có cùng name/ID.
5. Opcode thuộc đúng một capability.
6. Capability tồn tại trong capability model và được ít nhất một target hỗ trợ.
7. Opcode có VM dispatch case.
8. Resource binding, nếu có, phải tham chiếu public API/capability hợp lệ và khai báo policy cho toàn bộ target profiles.
9. Compiler registry không được expose API ngoài API SSoT.

## Runtime endpoint evidence

H34 phân loại endpoint từ từng VM case:

- `RobotAPI::<function>`: dispatch trực tiếp xuống Standard Robot API.
- `CooperativeLineOperation::<function>`: dispatch qua cooperative runtime service.
- `VM::ExecuteInstruction`: opcode được thực thi nội bộ trong VM hoặc là GUI/NOP semantics.

H34 chỉ yêu cầu public API có VM dispatch rõ ràng. Internal opcodes không thuộc public API trace chain và tiếp tục được kiểm soát bởi H32/H26 contracts.

## Machine-readable evidence

`tools/contract_traceability.py` sinh:

`.build/h34/contract-traceability.json`

Evidence gồm:

- source-of-truth paths;
- implementation evidence paths;
- summary counts;
- một trace row cho mỗi public API;
- capability/target/resource bindings;
- VM dispatch endpoint;
- danh sách contract errors.

Evidence phải có `status=PASS` và `error_count=0` để H34 gate pass.

## CI gates

H34 chạy như dedicated gate sau H33 và trước H26-A/H26-B cùng production ZIP build. Vì vậy contract drift sẽ fail sớm trước bước packaging nặng.

H34 cũng nằm trong `run_all_tests.py` để full repository regression luôn kiểm tra traceability.

## Fail-closed cases

H34 phải FAIL khi có một trong các tình huống:

- API có opcode không tồn tại trong canonical ISA;
- name/ID giữa API, canonical ISA và generated Opcode khác nhau;
- API thiếu compiler registry binding;
- compiler registry expose API không có trong API SSoT;
- opcode không thuộc capability hoặc thuộc nhiều capability;
- target profile tham chiếu capability không tồn tại;
- public API thiếu VM dispatch;
- resource binding trỏ tới API/capability không tồn tại;
- resource policy không phủ toàn bộ target profiles.

## Definition of Done

- Mọi public API có end-to-end trace row.
- H34 evidence JSON được sinh deterministic từ repository state.
- Dedicated H34 CI gate PASS.
- H34 được chạy trong full regression suite.
- H32/H33/H26 gates tiếp tục PASS.
- Không thay đổi production behavior và không thêm robot feature.
