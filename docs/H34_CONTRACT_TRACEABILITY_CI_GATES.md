# H34 — Contract Traceability + CI Gates

## Mục tiêu

H34 biến các contract đã được chuẩn hóa ở H32/H33 thành một chuỗi traceability có thể kiểm tra tự động:

`Robot API → compiler registry → compiler handler/lowering → canonical opcode/capability/target → emitted opcode → VM dispatch → runtime endpoint`

H34 không tạo thêm nguồn sự thật mới và không thêm tính năng robot. File JSON được sinh ra chỉ là evidence, không phải contract authority.

## Source of Truth

- Robot API: `robot-language/specification/api.yaml`
- Canonical ISA: `packages/robot-isa/canonical_isa.json`
- Capability model: `packages/robot-isa/capability_model.json`
- Target profiles/resources: `packages/robot-isa/target_profiles.json`

Implementation evidence:

- Compiler binding: `robot-compiler/compiler/generated/function_registry.py`
- Compiler lowering: `robot-compiler/compiler/handlers/*.py`
- Generated opcode enum: `robot-compiler/compiler/generated/opcode.py`
- Runtime dispatch: `robot-platform/main/src/Services/VM/VM.cpp`

## Traceability invariants

Mỗi public API phải thỏa tất cả điều kiện sau:

1. Có đúng một API definition trong `api.yaml`.
2. Logical opcode name và numeric ID khớp canonical ISA.
3. Có compiler binding trong generated function registry và binding dùng đúng logical opcode.
4. Compiler handler implementation phải tồn tại và actual lowering phải được phân tích từ handler source.
5. Generated Python Opcode enum có cùng logical name/ID.
6. Logical opcode thuộc đúng một capability.
7. Capability tồn tại trong capability model và được ít nhất một target hỗ trợ.
8. Mỗi opcode thực sự được compiler emit phải tồn tại trong generated opcode/canonical ISA và có VM dispatch case.
9. Resource binding, nếu có, phải tham chiếu public API/capability hợp lệ và khai báo policy cho toàn bộ target profiles.
10. Compiler registry không được expose API ngoài API SSoT.

## Semantic-aware lowering

H34 không giả định logical opcode luôn được emit trực tiếp.

- `Native`: compiler bắt buộc emit đúng logical opcode duy nhất. Nếu emit `Nop`, opcode khác hoặc không emit thì H34 FAIL.
- `Stub`: compiler có thể lower sang `Nop` hoặc implementation thay thế; evidence phải ghi đúng lowering thực tế.
- `Dummy`: compiler có thể lower sang opcode khác như `LoadConst`; evidence phải ghi đúng degradation.
- `Approximation`: compiler có thể lower sang implementation gần đúng; mọi emitted opcode vẫn phải trace tới VM.
- `NOP`: có thể không emit bytecode; trường hợp này được ghi `lowering_kind=no_emit` và không yêu cầu VM case giả.

Nhờ đó H34 không tạo false PASS kiểu logical `SetServo` có VM case trong khi compiler thực tế emit `Nop`, và cũng không tạo false FAIL cho GUI-only API không phát bytecode.

## Runtime endpoint evidence

Với mỗi emitted opcode, H34 phân loại endpoint từ VM case:

- `RobotAPI::<function>`: dispatch trực tiếp xuống Standard Robot API.
- `CooperativeLineOperation::<function>`: dispatch qua cooperative runtime service.
- `VM::ExecuteInstruction`: opcode được thực thi nội bộ trong VM.

API `no_emit` không có runtime endpoint vì compiler chủ động loại bỏ bytecode theo semantic contract.

## Machine-readable evidence

`tools/contract_traceability.py` sinh:

`.build/h34/contract-traceability.json`

Evidence schema v2 gồm:

- source-of-truth paths;
- implementation evidence paths;
- summary counts;
- một trace row cho mỗi public API;
- logical opcode/capability/target/resource bindings;
- compiler handler và `lowering_kind`;
- actual `emitted_opcodes`;
- VM dispatch/runtime endpoint cho từng emitted opcode;
- danh sách contract errors.

Evidence phải có `status=PASS` và `error_count=0` để H34 gate pass.

## CI gates

H34 chạy như dedicated gate sau H33 và trước H26-A/H26-B cùng production ZIP build. Vì vậy contract drift sẽ fail sớm trước bước packaging nặng.

H34 cũng nằm trong `run_all_tests.py` để full repository regression luôn kiểm tra traceability.

## Fail-closed cases

H34 phải FAIL khi có một trong các tình huống:

- API có logical opcode không tồn tại trong canonical ISA;
- name/ID giữa API, canonical ISA và generated Opcode khác nhau;
- API thiếu compiler registry binding;
- compiler handler không tồn tại;
- `Native` API không emit đúng logical opcode;
- compiler emit opcode không tồn tại trong generated/canonical ISA;
- emitted opcode không có VM dispatch;
- compiler registry expose API không có trong API SSoT;
- logical opcode không thuộc capability hoặc thuộc nhiều capability;
- target profile tham chiếu capability không tồn tại;
- resource binding trỏ tới API/capability không tồn tại;
- resource policy không phủ toàn bộ target profiles.

## Definition of Done

- Mọi public API có end-to-end trace row qua compiler lowering thực tế.
- Native APIs không được phép silently degrade.
- Stub/Dummy/Approximation/NOP APIs ghi đúng degradation/no-emit evidence.
- H34 evidence JSON được sinh deterministic từ repository state.
- Dedicated H34 CI gate PASS.
- H34 được chạy trong full regression suite.
- H32/H33/H26 gates tiếp tục PASS.
- Không thay đổi production behavior và không thêm robot feature.
