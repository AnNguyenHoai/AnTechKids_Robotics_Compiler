# Behavior Engine

## Overview
Behavior Engine là tầng điều phối các hành vi (behaviors) của robot. Behaviors là các đơn vị hành động có thể tái sử dụng, kết hợp cảm biến và chuyển động để tạo ra phản ứng thông minh.

## Architecture
Mission → Behavior Scheduler → Behavior → BehaviorContext → RobotAPI/Sensors → Hardware

## Components
- **Behavior**: Lớp cơ sở với lifecycle: init, start, update, pause, resume, stop, reset.
- **BehaviorContext**: Cung cấp quyền truy cập đến các dịch vụ runtime (motion, sensors, state).
- **BehaviorScheduler**: Quản lý danh sách behaviors, chạy tuần tự, hỗ trợ timeout và interruption.
- **Built-in Behaviors**: MoveForward, MoveBackward, TurnLeft, TurnRight, Stop, Wait.
- **Reactive Behaviors**: TouchStop, ObstacleStop, LightTrigger, LineDetect, ColorDetect.

## Usage
- Qua Serial: gửi lệnh `behavior start`, `behavior list`, `behavior run <index>`.
- Trong code: tạo scheduler, add behavior, gọi start() và update() trong loop.

## Lifecycle
- CREATED → INITIALIZED → RUNNING → COMPLETED/FAILED/INTERRUPTED/CANCELLED