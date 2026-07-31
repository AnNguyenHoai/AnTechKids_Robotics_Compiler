# Sprint S2 -- HAL Framework v1 Foundation

**Assignee:** DeepSeek\
**Priority:** Critical\
**Type:** Architecture Foundation\
**Prerequisite:** Sensor Framework v1 Merged

------------------------------------------------------------------------

# Background

Sensor Framework v1 đã được merge thành công và chứng minh khả năng mở
rộng.

Hiện tại các driver vẫn phụ thuộc trực tiếp vào Arduino API (`pinMode`,
`digitalWrite`, `digitalRead`, `pulseIn`, `analogRead`...).

Điều này khiến Robot Platform bị khóa vào Arduino và gây khó khăn khi
chuyển sang ESP-IDF, STM32 hoặc Linux.

Sprint S2 sẽ xây dựng **HAL (Hardware Abstraction Layer)** -- lớp trừu
tượng phần cứng dùng chung cho toàn bộ Robot Platform.

------------------------------------------------------------------------

# Goal

Xây dựng HAL Framework v1 để:

-   Tách toàn bộ driver khỏi Arduino API.
-   Chuẩn bị hỗ trợ nhiều nền tảng phần cứng.
-   Không làm thay đổi public API của Sensor Framework.

------------------------------------------------------------------------

# Scope

## Task 1 -- HAL Architecture

Thiết kế kiến trúc:

``` text
Application
↓
RobotAPI
↓
Framework
↓
Driver
↓
HAL
↓
Platform
```

Tài liệu hóa trách nhiệm của từng layer.

------------------------------------------------------------------------

## Task 2 -- GPIO HAL

Thiết kế giao diện GPIO:

Ví dụ:

-   pinMode()
-   digitalWrite()
-   digitalRead()
-   analogRead()

Driver chỉ được sử dụng HAL, không gọi Arduino trực tiếp.

------------------------------------------------------------------------

## Task 3 -- Timing HAL

Thiết kế API:

-   delayMs()
-   delayUs()
-   millis()
-   micros()

Không gọi `delay()` hoặc `delayMicroseconds()` trực tiếp trong driver.

------------------------------------------------------------------------

## Task 4 -- Pulse HAL

Thiết kế abstraction cho:

-   pulseIn()

Mục tiêu là để Ultrasonic không còn phụ thuộc Arduino.

------------------------------------------------------------------------

## Task 5 -- Platform Layer

Tạo Platform Arduino đầu tiên.

Ví dụ:

``` text
Platform/
    Arduino/
```

Chỉ layer này được phép include:

``` cpp
Arduino.h
```

------------------------------------------------------------------------

## Task 6 -- Refactor Existing Drivers

Refactor:

-   TCRT5000
-   Ultrasonic

để chỉ sử dụng HAL.

Không thay đổi hành vi.

------------------------------------------------------------------------

## Task 7 -- Validation

Kiểm tra:

-   Sensor Framework vẫn hoạt động.
-   RobotAPI không thay đổi.
-   Python API không thay đổi.

------------------------------------------------------------------------

# Deliverables

## Source

``` text
HAL/
├── GPIOHal.h
├── TimeHal.h
├── PulseHal.h

Platform/
└── Arduino/
```

## Documentation

Tạo:

-   HAL_ARCHITECTURE.md
-   HAL_API_SPEC.md
-   PLATFORM_ADAPTER_GUIDE.md

Bao gồm:

-   Layer Diagram
-   Dependency Rules
-   Design Decisions
-   Porting Strategy

------------------------------------------------------------------------

# Acceptance Criteria

-   Không còn driver nào include `Arduino.h`.
-   Chỉ Platform layer được phép phụ thuộc Arduino.
-   Sensor Framework hoạt động bình thường.
-   RobotAPI và VM không thay đổi.
-   HAL đủ khả năng mở rộng sang ESP-IDF và STM32.

------------------------------------------------------------------------

# Constraints

-   Không bổ sung tính năng mới.
-   Không thay đổi public API nếu không có lý do kiến trúc.
-   Ưu tiên kiến trúc sạch và khả năng porting.

------------------------------------------------------------------------

# Merge Policy

Sau khi hoàn thành, gửi:

1.  HAL Architecture Report
2.  Dependency Diagram
3.  Platform Layer Diagram
4.  Danh sách driver đã chuyển sang HAL
5.  Migration Notes

Chỉ merge sau Architecture Review.
