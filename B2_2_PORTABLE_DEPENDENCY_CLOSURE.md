# B2.2 — Portable Dependency Closure

## 1. Mục tiêu

B2.2 chứng minh rằng RoboStudio production artifact không cần và không được âm thầm sử dụng Python, Node, PlatformIO, compiler hoặc development tool đã cài trên máy host.

Mục tiêu của giai đoạn này là khóa dependency boundary trước khi chuyển sang kiểm thử path/state, USB/COM và flash phần cứng.

## 2. Contract

Khi chạy từ production ZIP đã giải nén:

1. Runtime/tool của ứng dụng phải resolve từ bên trong application root.
2. `PATH` của child process không kế thừa các thư mục development/global từ máy host.
3. Trên Windows chỉ giữ lại application-owned directories và system allow-list tối thiểu (`System32`, `SystemRoot`).
4. Các biến môi trường có thể inject Python/Node/PlatformIO từ host bị xóa hoặc ghi đè bằng đường dẫn trong artifact.
5. Top-level executable của production compile/launch phải nằm trong artifact; truyền trực tiếp absolute path tới tool ngoài artifact cũng bị từ chối.
6. Nếu dependency bắt buộc bị thiếu, hệ thống fail fast với diagnostic rõ ràng và không fallback sang host `PATH`.
7. Production E2E report phải lưu evidence cho dependency-closure mode và PATH ownership.
8. Regression/CI phải fail nếu B2.2 contract bị phá vỡ.

## 3. Thay đổi implementation

### `tools/dependency_closure.py`

Là policy chung cho executable/runtime dependency closure:

- tạo artifact-closed environment;
- loại bỏ host Python/Conda/Node/npm/PlatformIO injection variables;
- xây dựng PATH từ application-owned executable directories;
- chỉ giữ OS allow-list tối thiểu trên Windows;
- kiểm tra ownership của executable;
- fail fast nếu required dependency không có trong artifact;
- tạo evidence để đưa vào production acceptance report.

### `tools/production_e2e.py`

Production E2E sử dụng closed environment trước khi launch/compile và kiểm tra top-level command executable thuộc artifact.

Điều này đóng lỗ hổng trước đây: dù `{python}`/compiler được tìm trong artifact, child process vẫn có thể kế thừa host `PATH` và gọi nhầm tool toàn cục.

### `tests/b2_2/run_b2_2.py`

Regression suite tạo một hostile host environment và kiểm tra:

- host PATH bị loại bỏ;
- Python/Node/PlatformIO injection bị loại bỏ hoặc rebinding;
- executable cùng tên trong artifact được ưu tiên;
- khi xóa executable trong artifact, executable cùng tên trên host không được dùng thay thế;
- explicit host absolute executable bị từ chối;
- production E2E lưu dependency closure evidence.

### CI

`tests/b2_2/run_b2_2.py` được chạy trực tiếp trong GitHub Actions và cũng được đưa vào `run_all_tests.py`.

Workflow chạy cho cả `push` và `pull_request` vào `main`, để dependency closure thực sự trở thành merge gate thay vì chỉ phát hiện sau khi đã merge.

## 4. Acceptance Criteria

B2.2 PASS khi tất cả điều kiện sau đúng:

- [x] Host `PATH` không được kế thừa vào production child process.
- [x] Python/runtime path của production artifact là application-owned.
- [x] PlatformIO runtime directories được rebound về artifact.
- [x] Host Python/Conda/Node/npm/PlatformIO injection variables bị loại bỏ.
- [x] Production top-level launch/compile executable bắt buộc application-owned.
- [x] Missing artifact dependency fail fast; host fallback bị cấm.
- [x] Production E2E report có dependency closure evidence.
- [x] B2.2 regression test nằm trong repository-wide test gate.
- [x] GitHub Actions chạy B2.2 trên Pull Request vào `main`.

## 5. Không thuộc B2.2

Các nội dung dưới đây cố ý để cho các bước tiếp theo:

- B2.3: path relocation, Unicode/space path và user-state isolation;
- B2.4: USB/COM/driver/hardware detection và flash portability;
- B2.5: real clean-machine end-to-end với robot thật;
- B2.6: release/copy-and-run contract, manifest/checksum/user guide hoàn chỉnh.

## 6. Definition of Done của B2.2

Một máy có Python/Node/PlatformIO/toolchain global hoặc có hostile PATH không được ảnh hưởng tới executable/runtime dependency resolution của RoboStudio production artifact. Nếu artifact thiếu dependency cần thiết, acceptance gate phải FAIL thay vì vô tình sử dụng dependency trên máy host.
