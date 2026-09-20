# Hardware Runtime Path Contract

## Mục tiêu

RoboStudio source-development và `RoboStudio.exe` phải dùng cùng một contract cho cấu hình phần cứng. Không được có hai bản `generated_device_config.h` cạnh tranh nhau giữa repository và AppData.

## Source of truth

Cấu hình phần cứng người dùng được lưu tại:

```text
<ROBOSTUDIO_STATE_ROOT>/hardware.json
```

Trên Windows mặc định:

```text
%LOCALAPPDATA%/RoboStudio/hardware.json
```

`hardware.json` là source of truth. `generated_device_config.h` chỉ là derived artifact.

## Generated user header

Cả source mode và packaged EXE đều generate tại:

```text
<ROBOSTUDIO_STATE_ROOT>/generated/generated_device_config.h
```

RoboStudio không ghi user hardware state vào repository hoặc production release.

## Firmware template

File sau vẫn tồn tại trong firmware source/release:

```text
robot-platform/main/include/generated/generated_device_config.h
```

Trong source repository đây là default firmware template, không phải current user state.

Trong packaged release, firmware template cũng được coi là immutable.

## Deployment flow

Mọi build/USB/OTA/bootstrap từ RoboStudio phải thực hiện:

```text
hardware.json
    -> regenerate generated_device_config.h
    -> prepare isolated firmware workspace
    -> overlay freshly generated header
    -> PlatformIO build/upload
```

Deployment không được tin một generated header cũ chỉ vì file đó đang tồn tại.

## Runtime modes

### Development/source

- application root: repository root;
- firmware template: `<repo>/robot-platform`;
- mutable hardware config: user state root;
- generated user header: user state root;
- build workspace: isolated writable build state.

### Packaged EXE

- application root: folder chứa `RoboStudio.exe`;
- firmware template: `<application>/firmware/robot-platform`;
- mutable hardware config: external user state root;
- generated user header: external user state root;
- build workspace: isolated external writable state.

Khác biệt giữa hai mode chỉ nằm ở application/template root. Mutable hardware state dùng cùng contract.

## Safety properties

- path có dấu cách hoặc Unicode phải được hỗ trợ bằng `pathlib`/argument-safe subprocess handling;
- packaged mode không được ghi vào application/release root;
- source mode không được mutate firmware template khi user bấm Apply Configuration;
- stale generated header phải bị regenerate từ `hardware.json` trước deployment;
- feature metadata/defaults/header rendering phải dùng shared contract giữa RoboStudio UI và packaged deployment Python.

## Regression

`tests/b2_3/run_hardware_runtime_path_contract.py` khóa các trường hợp:

- source mode dùng external state;
- packaged mode dùng external state;
- repository/release firmware template không đổi;
- stale AppData header không thể thắng `hardware.json`;
- staging nhận freshly regenerated header;
- path có space như `EASTVN - An Nguyen` hoạt động đúng.
