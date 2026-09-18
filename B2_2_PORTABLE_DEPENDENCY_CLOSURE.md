# B2.2 — Portable Dependency Closure

## 1. Mục tiêu

B2.2 chứng minh rằng RoboStudio production artifact không cần và không được âm thầm sử dụng Python, Node, PlatformIO, compiler hoặc development tool đã cài trên máy host.

Mục tiêu của giai đoạn này là khóa dependency boundary trước khi chuyển sang kiểm thử path/state, USB/COM và flash phần cứng.

## 2. Contract

Khi chạy từ production ZIP đã giải nén:

1. Runtime/tool của ứng dụng phải resolve từ bên trong application root.
2. `PATH` của process production không kế thừa các thư mục development/global từ máy host.
3. Trên Windows chỉ giữ lại application-owned directories và system allow-list tối thiểu (`System32`, `SystemRoot`).
4. Các biến môi trường có thể inject Python/Node/PlatformIO từ host bị xóa hoặc ghi đè bằng đường dẫn trong artifact.
5. Top-level executable của production compile/launch phải nằm trong artifact; truyền trực tiếp absolute path tới tool ngoài artifact cũng bị từ chối.
6. Portable Python phải chứa runtime DLL và standard library cần để tự bootstrap; chỉ copy `python.exe` không được xem là dependency-complete.
7. Nếu dependency bắt buộc bị thiếu, hệ thống fail fast với diagnostic rõ ràng và không fallback sang host `PATH`.
8. Production E2E report phải lưu evidence cho dependency-closure mode và PATH ownership.
9. Startup bootstrap, clean-machine launcher và deployment runtime phải dùng cùng dependency-closure policy; không chỉ acceptance test.
10. Regression/CI phải fail nếu B2.2 contract bị phá vỡ.
11. Final subprocess boundary phải tự áp dependency closure. Caller không được bypass contract bằng `env=os.environ.copy()` hoặc bằng cách bỏ trống `env`.
12. Python helper script trong frozen RoboStudio phải chạy bằng portable Python trong artifact; `sys.executable` không được dùng như Python interpreter vì ở packaged build nó là RoboStudio executable.
13. Dependency closure phải tiếp tục có hiệu lực sau khi frozen RoboStudio chuyển quyền thực thi sang portable Python. Marker `ROBOSTUDIO_DEPENDENCY_MODE=artifact-closed` là contract truyền trạng thái sang compiler/PlatformIO/flash child process tiếp theo.
14. Portable Python production phải tắt user-site package loading (`PYTHONNOUSERSITE=1`) và bytecode write (`PYTHONDONTWRITEBYTECODE=1`) để không lấy package/state từ profile của máy host.

## 3. Thay đổi implementation

### `tools/dependency_closure.py`

Policy chung cho executable/runtime dependency closure:

- tạo artifact-closed environment;
- loại bỏ host Python/Conda/Node/npm/PlatformIO injection variables;
- xây dựng PATH từ application-owned executable directories;
- chỉ giữ OS allow-list tối thiểu trên Windows;
- kiểm tra ownership của executable;
- fail fast nếu required dependency không có trong artifact;
- tạo evidence cho production acceptance report;
- set `PYTHONNOUSERSITE=1` để portable Python không đọc user-site package của máy host;
- set `PYTHONDONTWRITEBYTECODE=1` để production runtime không tạo Python bytecode vào vị trí không thuộc runtime state contract.

### `tools/runtime_bootstrap.py`

Frozen RoboStudio bootstrap dùng artifact-closed environment ngay từ startup. Source/development mode vẫn giữ nguyên developer environment.

Việc này đóng lỗ hổng mà bootstrap trước đây pin PlatformIO về artifact nhưng vẫn giữ nguyên host `PATH`.

### `tools/distribution_launch.py`

Clean-machine launcher dùng cùng dependency-closure policy. RoboStudio được gọi bằng absolute path, nhưng child environment không còn chứa global/developer PATH. Launch manifest ghi rõ `artifact-closed-with-windows-system-allowlist`.

### `tools/deployment_runtime.py`

Đây là runtime boundary thật của compile/PlatformIO/flash. Khi RoboStudio chạy ở frozen/packaged mode, deployment subprocess sử dụng artifact-closed environment. Source/development mode vẫn giữ developer environment để không phá workflow phát triển.

B2.2 hardening khóa policy tại chính `run_process()` ngay trước `subprocess.Popen()`:

- caller truyền `os.environ.copy()` vẫn bị seal lại;
- caller không truyền `env` cũng không được kế thừa host environment trong production mode;
- executable được validate là application-owned trước khi spawn;
- host absolute executable bị từ chối trước `Popen`;
- các application value hợp lệ như Wi-Fi/OTA credential vẫn được giữ lại;
- `python_command()` resolve portable Python và chuyển lỗi thiếu packaged interpreter thành deployment diagnostic rõ ràng;
- `_dependency_closed_mode()` nhận biết cả frozen RoboStudio lẫn portable-Python descendants có marker `ROBOSTUDIO_DEPENDENCY_MODE=artifact-closed`;
- vì vậy closure được truyền xuyên suốt chuỗi `RoboStudio -> portable Python -> PlatformIO/flash`, thay vì mất hiệu lực ngay khi process thứ hai không còn `sys.frozen=True`.

Điểm này quan trọng vì dependency closure chỉ ở helper/environment builder là chưa đủ: production caller có thể vô tình bỏ qua helper và mở lại host PATH tại subprocess boundary. Tương tự, chỉ kiểm tra `sys.frozen` là chưa đủ vì portable Python helper không phải PyInstaller process.

### `robostudio/services/robot_deployment_service.py`

Các Python helper `bootstrap_config.py` và `deploy_robot.py` không còn chạy bằng `sys.executable`. Service sử dụng `deployment_runtime.python_command()` để:

- source/dev mode vẫn dùng Python interpreter của developer;
- frozen mode bắt buộc dùng Python nằm trong artifact;
- thiếu portable Python thì fail fast thay vì relaunch RoboStudio executable hoặc fallback sang host Python.

### `tools/production_distribution.py`

Production builder từ chối portable Python không dependency-complete:

- bắt buộc có `python.exe`;
- bắt buộc có Python runtime DLL (`python*.dll`);
- bắt buộc có standard library bootstrap (`Lib/encodings` hoặc `python*.zip`);
- vẫn bắt buộc bundled PlatformIO Python package.

Nhờ vậy lỗi kiểu `0xC0000135 / DLL not found` bị chặn trước khi tạo production distribution thay vì chỉ xuất hiện trên máy sạch.

### `tools/clean_machine_e2e.py`

Clean-machine probe dùng chung dependency-closure policy và kiểm tra trong process thật rằng:

- bundled Python là application-owned;
- `PATH` chỉ chứa artifact-owned directories và Windows system allow-list;
- Python/Node/npm/PlatformIO host injection không lọt vào process;
- PlatformIO directories trỏ về artifact.

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
- packaged deployment runtime sử dụng closed environment;
- source/development runtime vẫn giữ developer PATH;
- production E2E lưu dependency closure evidence;
- `run_process()` seal caller-supplied hostile environment ngay tại spawn boundary;
- `run_process(env=None)` không kế thừa host PATH trong frozen mode;
- host absolute executable bị reject trước khi `Popen` được gọi;
- deployment helper script resolve packaged Python;
- RoboStudio deployment service không quay lại `sys.executable` cho Python helper scripts;
- portable Python không dùng user-site package của máy host.

### `tests/b2_2/run_portable_child_closure.py`

Regression riêng mô phỏng process portable Python không có `sys.frozen=True` nhưng được frozen RoboStudio launch với marker dependency closure. Test cố tình đầu độc lại `PATH/PYTHONPATH` và xác minh:

- marker production khiến child runtime re-seal environment trước `Popen`;
- explicit contaminated env không thể mở lại host PATH;
- `env=None` cũng không thể kế thừa lại host PATH/PYTHONPATH;
- marker `artifact-closed` tiếp tục được truyền cho process kế tiếp.

### Regression contracts

Các regression suite liên quan được cập nhật để phản ánh contract mới:

- `RSD-04`: frozen deployment đóng host PATH;
- `RSD-05`: frozen startup bootstrap đóng host PATH và Python user-site;
- `RSD-08`: clean-machine launch đóng host PATH, Python user-site và ghi path policy;
- `RSD-17`: production builder bắt runtime DLL/stdlib bị thiếu;
- `RSD-21.5`: E2E fixture staging một Python runtime thực sự runnable thay vì chỉ copy `python.exe`.

Các path assertion trên Windows so sánh bằng canonical/resolved path thay vì raw string, vì dependency-closure policy cố ý normalize case/path trước khi đưa vào production environment.

### CI

`tests/b2_2/run_b2_2.py` và `tests/b2_2/run_portable_child_closure.py` được chạy trực tiếp trong GitHub Actions và cũng được đưa vào `run_all_tests.py`.

Workflow chạy cho cả `push` và `pull_request` vào `main`, để dependency closure thực sự trở thành merge gate thay vì chỉ phát hiện sau khi đã merge.

## 4. Acceptance Criteria

B2.2 PASS khi tất cả điều kiện sau đúng:

- [x] Host `PATH` không được kế thừa vào production child process.
- [x] Frozen startup bootstrap và distribution launcher cũng đóng host PATH.
- [x] Python/runtime path của production artifact là application-owned.
- [x] Production builder từ chối Python payload thiếu runtime DLL hoặc standard library.
- [x] PlatformIO runtime directories được rebound về artifact.
- [x] Host Python/Conda/Node/npm/PlatformIO injection variables bị loại bỏ.
- [x] Frozen deployment runtime dùng dependency closure; source/dev mode vẫn giữ developer environment.
- [x] Production top-level launch/compile executable bắt buộc application-owned.
- [x] Missing artifact dependency fail fast; host fallback bị cấm.
- [x] Clean-machine runtime probe xác minh closure trong child process thật.
- [x] Production E2E report có dependency closure evidence.
- [x] B2.2 regression test nằm trong repository-wide test gate.
- [x] GitHub Actions chạy B2.2 trên Pull Request vào `main`.
- [x] Final production subprocess boundary tự seal caller environment trước `Popen`.
- [x] `env=None` trong production mode không còn đồng nghĩa với host-environment inheritance.
- [x] Host absolute executable bị chặn trước spawn.
- [x] RoboStudio deployment helper scripts dùng packaged Python thay cho `sys.executable`.
- [x] Dependency closure được propagate từ frozen RoboStudio qua portable Python tới nested PlatformIO/flash subprocess.
- [x] Portable Python production tắt user-site loading và bytecode write.

## 5. Không thuộc B2.2

Các nội dung dưới đây cố ý để cho các bước tiếp theo:

- B2.3: path relocation, Unicode/space path và user-state isolation;
- B2.4: USB/COM/driver/hardware detection và flash portability;
- B2.5: real clean-machine end-to-end với robot thật;
- B2.6: release/copy-and-run contract, manifest/checksum/user guide hoàn chỉnh.

## 6. Definition of Done của B2.2

Một máy có Python/Node/PlatformIO/toolchain global hoặc có hostile PATH không được ảnh hưởng tới executable/runtime dependency resolution của RoboStudio production artifact. Nếu artifact thiếu dependency cần thiết, build/acceptance gate phải FAIL thay vì vô tình sử dụng dependency trên máy host.

Definition này áp dụng tại process-launch boundary thật, không chỉ ở environment builder hoặc acceptance harness. Frozen RoboStudio phải tự enforce closure ngay trước mỗi deployment subprocess, phải chạy Python helper bằng interpreter nằm trong production artifact, và closure phải tiếp tục được enforce trong các portable-Python descendant process cho đến PlatformIO/flash boundary.
