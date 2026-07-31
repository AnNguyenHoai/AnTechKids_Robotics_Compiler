# Sprint S0.5 - Sensor Framework Architecture Refactor

**Assignee:** DeepSeek\
**Priority:** Critical\
**Type:** Architecture Refactoring\
**Prerequisite:** Sprint S0 Completed

------------------------------------------------------------------------

# Background

Sprint S0 đã hoàn thành và framework hoạt động. Tuy nhiên sau
Architecture Review, framework **chưa đủ chất lượng để trở thành nền
tảng lâu dài của Robot Platform**.

Hiện implementation hiện tại mới giải quyết bài toán **TCRT5000**, chưa
giải quyết bài toán **Sensor Framework**.

Mục tiêu của Sprint S0.5 là **không thêm tính năng mới**, mà **nâng cấp
kiến trúc** trước khi merge.

------------------------------------------------------------------------

# Goal

Xây dựng **Sensor Framework v1** đủ khả năng mở rộng cho:

-   TCRT5000
-   Ultrasonic
-   Button
-   Touch
-   Encoder
-   IMU
-   Color Sensor
-   Future Sensors

mà không cần refactor lại kiến trúc.

------------------------------------------------------------------------

# Scope

## Task 1 - Refactor ISensor

### Problem

Hiện tại:

``` cpp
virtual int read() = 0;
```

Đây là abstraction chưa phù hợp vì mọi sensor bị ép trả về `int`.

### Required

ISensor chỉ nên định nghĩa:

-   initialize()
-   update()
-   healthy()
-   type()
-   name()

Không ép mọi sensor có cùng API đọc dữ liệu.

------------------------------------------------------------------------

## Task 2 - Introduce Sensor Categories

Thiết kế phân tầng:

``` text
ISensor
├── DigitalSensor
├── AnalogSensor
├── DistanceSensor
├── MotionSensor
└── Future Sensors
```

Ví dụ:

``` text
DigitalSensor
├── Button
├── Touch
└── TCRT5000
```

------------------------------------------------------------------------

## Task 3 - Refactor TCRT5000 API

Không expose:

-   HIGH
-   LOW

API mong muốn:

-   isLineDetected()
-   rawLevel()
-   setThreshold()
-   getThreshold()

RobotAPI chỉ sử dụng semantic API.

------------------------------------------------------------------------

## Task 4 - Sensor Identification

Thay string lookup bằng:

``` cpp
enum class SensorID
```

Ví dụ:

-   LeftLine
-   CenterLine
-   RightLine

Mục tiêu:

-   Compile-time safety
-   Lookup nhanh
-   Không dùng string runtime

------------------------------------------------------------------------

## Task 5 - Lifecycle

Chuẩn hóa lifecycle:

``` text
Create
↓
Register
↓
Initialize
↓
Update
↓
Shutdown
```

SensorManager phải quản lý đầy đủ vòng đời này.

------------------------------------------------------------------------

## Task 6 - Health Model

Nếu `healthy()` chưa có ý nghĩa:

-   Implement đầy đủ
-   Hoặc loại bỏ khỏi interface

Không giữ dead API.

------------------------------------------------------------------------

## Task 7 - Calibration Support

Thiết kế framework hỗ trợ:

-   Threshold
-   Invert
-   Calibration

Chưa cần triển khai đầy đủ nhưng phải có điểm mở trong kiến trúc.

------------------------------------------------------------------------

## Task 8 - Merge Existing Sensor Architecture

Hiện project tồn tại song song:

``` text
Devices/
Sensor/
```

Đánh giá và đề xuất một kiến trúc thống nhất.

Không để hai framework cảm biến cùng tồn tại.

------------------------------------------------------------------------

## Task 9 - Dependency Review

Đảm bảo dependency một chiều:

``` text
Application
↓
RobotAPI
↓
Sensor Framework
↓
Sensor Driver
↓
HAL
↓
GPIO
```

Không có dependency ngược.

------------------------------------------------------------------------

# Deliverables

## Source Code

Refactor toàn bộ Sensor Framework.

## Documentation

Tạo:

-   SENSOR_FRAMEWORK_V1.md

Bao gồm:

-   Architecture
-   Layer Design
-   Dependency Diagram
-   Class Hierarchy
-   Lifecycle
-   Design Decisions

## Class Diagram

Bao gồm tối thiểu:

``` text
ISensor
↓
DigitalSensor
↓
TCRT5000
```

và các nhóm sensor còn lại.

## Future Expansion Plan

Mô tả cách framework mở rộng sang:

-   Ultrasonic
-   Touch
-   Encoder
-   IMU

mà không cần refactor.

------------------------------------------------------------------------

# Acceptance Criteria

-   ISensor không còn ép mọi sensor trả về `int`.
-   Sensor được phân loại theo chức năng.
-   RobotAPI chỉ nhìn thấy semantic API.
-   Không expose GPIO logic.
-   Chỉ còn một kiến trúc sensor trong project.
-   Lifecycle hoàn chỉnh.
-   Có khả năng mở rộng mà không thay đổi kiến trúc.

------------------------------------------------------------------------

# Constraints

-   Không thêm feature ngoài phạm vi refactor.
-   Không phá vỡ public API hiện có nếu không thực sự cần thiết.
-   Mọi thay đổi phải có lý do thiết kế rõ ràng.

------------------------------------------------------------------------

# Merge Policy

Không merge trực tiếp.

Sau khi hoàn thành, gửi lại:

1.  Architecture Review
2.  Class Diagram
3.  Dependency Diagram
4.  Public API
5.  Design Decisions & Trade-offs

Chỉ merge sau khi được review và phê duyệt.
