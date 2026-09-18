# B2.7 – One-Click Production ZIP

## Mục tiêu

Từ một checkout source hợp lệ trên Windows, người build chỉ cần chạy:

```bat
BUILD_PRODUCTION_ZIP.cmd
```

Script tự chuẩn bị toàn bộ input mà B2.6 cần và xuất production ZIP cuối cùng.

## Luồng tự động

1. Tự tìm Python 64-bit 3.10–3.13 trên máy build; ưu tiên Python 3.10.
2. Tạo/reuse `.build/production/build-venv`.
3. Cài build-only dependencies từ `scripts/production-build-requirements.txt`.
4. Build `RoboStudio.exe` bằng PyInstaller.
5. Tự tìm Python portable đã cache; nếu chưa có, tải Python 3.10.11 embeddable từ python.org.
6. Tạo runtime Python sạch trong staging và cài PlatformIO Core 6.1.18 + PyYAML.
7. Đọc pin platform trực tiếp từ `robot-platform/platformio.ini` (`espressif32@6.12.0`).
8. Dùng chính firmware production `env:esp32dev` để provision PlatformIO platform/packages/toolchain vào cache.
9. Chỉ copy `platforms/` và `packages/` sạch sang runtime artifact; build cache không vào ZIP.
10. Copy `packages/robot-isa/target_profiles.json` sang runtime resources.
11. Tự lấy `git rev-parse HEAD` và `VERSION`.
12. Gọi `tools/one_command_production_build.py`, sau đó B2.6 finalizer khóa copy-run contract, manifest, provenance và portable proof.
13. Xuất:

```text
releases/production/RoboStudio-<VERSION>-Windows.zip
```

## Cách dùng thông thường

Double-click:

```text
BUILD_PRODUCTION_ZIP.cmd
```

Hoặc chạy từ Command Prompt:

```bat
BUILD_PRODUCTION_ZIP.cmd
```

## Các option hữu ích

Làm sạch staging rồi build lại:

```bat
BUILD_PRODUCTION_ZIP.cmd --clean
```

Giữ staging để debug:

```bat
BUILD_PRODUCTION_ZIP.cmd --keep-work
```

Chỉ dùng cache, tuyệt đối không tải mạng:

```bat
BUILD_PRODUCTION_ZIP.cmd --offline
```

Xem plan mà không thay đổi file:

```bat
BUILD_PRODUCTION_ZIP.cmd --plan
```

Cho phép build khi tracked source đang sửa dở (không khuyến nghị cho release):

```bat
BUILD_PRODUCTION_ZIP.cmd --allow-dirty
```

## Cache

Mặc định:

```text
.build/production/cache/
```

Có thể đổi bằng environment variable:

```text
ROBOSTUDIO_BUILD_CACHE
```

Có thể chỉ định Python build cụ thể bằng:

```text
ROBOSTUDIO_BUILD_PYTHON
```

Có thể chỉ định một Python portable đã có bằng:

```text
ROBOSTUDIO_PORTABLE_PYTHON_ROOT
```

Không cần đặt các biến này trong luồng thông thường.

## Prerequisite máy build

- Windows 64-bit.
- Python 64-bit 3.10–3.13 để bootstrap quá trình build. Script tự tìm; không cần nhập path.
- Git có trong PATH để lấy source revision.
- Internet ở lần build đầu để tải Python embeddable, PyPI packages và ESP32 PlatformIO packages. Những lần sau có thể dùng cache/offline.

Các prerequisite trên chỉ thuộc **máy tạo release**. Chúng không trở thành prerequisite của máy người dùng chạy production ZIP.

## Fail-closed

Production build dừng nếu:

- thiếu source input quan trọng;
- tracked source bị sửa nhưng chưa commit/stash;
- không có Python build phù hợp;
- PyInstaller không tạo `RoboStudio.exe`;
- portable Python không đủ `python.exe`/DLL/stdlib;
- PlatformIO platform không pin exact version;
- không provision đủ `platforms/` + `packages/`;
- B2.6 release finalizer/portable proof/copy-run contract fail;
- ZIP cuối không tồn tại ở tên/version dự kiến.

## Kết quả cuối

Sau PASS, terminal in:

- đường dẫn ZIP;
- SHA-256;
- đường dẫn `.build/production/one-click-build-report.json`.

File ZIP cuối vẫn tuân theo B2.2–B2.6: runtime thuộc artifact, mutable state nằm ngoài release, không phụ thuộc Python/PlatformIO/dev environment của máy đích.
