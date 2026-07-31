# Sprint S1.1 - Ultrasonic Framework Cleanup

**Assignee:** DeepSeek\
**Priority:** High\
**Type:** Architecture Cleanup\
**Prerequisite:** Sprint S1 Completed

------------------------------------------------------------------------

# Background

Sprint S1 đã chứng minh Sensor Framework có thể mở rộng thành công sang
Ultrasonic mà không phải sửa kiến trúc lõi.

Tuy nhiên Architecture Review phát hiện một số vấn đề trong
implementation cần xử lý trước khi merge chính thức.

Sprint này chỉ tập trung **làm sạch kiến trúc**, không bổ sung tính năng
mới.

------------------------------------------------------------------------

# Goal

Hoàn thiện implementation của Ultrasonic để đáp ứng tiêu chuẩn Robot
Platform.

------------------------------------------------------------------------

# Task 1 -- Remove Duplicate Ultrasonic

## Problem

Hiện project vẫn tồn tại:

``` text
Devices/
    Ultrasonic

Sensor/
    Ultrasonic
```

Điều này tạo duplicate implementation.

## Required

-   Chỉ giữ **một** Ultrasonic implementation.
-   Thống nhất include path.
-   Loại bỏ code và tài liệu dư thừa.
-   Đảm bảo không còn hai kiến trúc song song.

------------------------------------------------------------------------

# Task 2 -- Improve Health Model

## Problem

Framework chưa phân biệt:

-   Không phát hiện vật cản.
-   Cảm biến lỗi.

## Required

Thiết kế health model rõ ràng.

Ví dụ:

-   Echo timeout ngắn → không có vật cản.
-   Echo timeout liên tiếp nhiều lần → sensor unhealthy.

Giải thích rõ tiêu chí trong tài liệu.

------------------------------------------------------------------------

# Task 3 -- Simplify DistanceSensor API

Rà soát:

``` cpp
unit()
maxRangeCm()
```

Nếu chưa tạo giá trị thực tế:

-   loại bỏ,
-   hoặc chuyển thành hằng số / constexpr.

Mục tiêu là giữ API nhỏ và rõ ràng.

------------------------------------------------------------------------

# Task 4 -- Layer Boundary Review

Kiểm tra lại vai trò của:

-   Sensor Framework
-   Sensor Driver
-   HAL

Đảm bảo trách nhiệm từng layer rõ ràng.

Tài liệu cần mô tả:

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

Giải thích vì sao Ultrasonic hiện đang ở vị trí đó và kế hoạch tiến hóa
trong tương lai.

------------------------------------------------------------------------

# Deliverables

## Source Code

-   Dọn dẹp toàn bộ implementation Ultrasonic.
-   Loại bỏ duplicate source.

## Documentation

Tạo:

-   ULTRASONIC_REVIEW_FIX.md
-   SENSOR_LAYER_GUIDELINE.md

Trong đó trình bày:

-   Các thay đổi.
-   Quyết định kiến trúc.
-   Lý do lựa chọn.

------------------------------------------------------------------------

# Acceptance Criteria

-   Chỉ còn một Ultrasonic implementation.
-   Health model có ý nghĩa.
-   API DistanceSensor gọn và nhất quán.
-   Layer responsibility được mô tả rõ.
-   Không phát sinh thay đổi đối với ISensor và Sensor Framework v1.

------------------------------------------------------------------------

# Merge Policy

Sau khi hoàn thành:

1.  Gửi Architecture Review Summary.
2.  Gửi danh sách file đã loại bỏ.
3.  Gửi Dependency Diagram cập nhật.

Chỉ merge sau khi review đạt yêu cầu.
