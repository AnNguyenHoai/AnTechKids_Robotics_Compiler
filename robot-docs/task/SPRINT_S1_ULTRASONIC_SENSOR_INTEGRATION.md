# Sprint S1 - Ultrasonic Sensor Integration

**Assignee:** DeepSeek\
**Priority:** High\
**Type:** Feature + Architecture Validation\
**Prerequisite:** Sensor Framework v1 merged

------------------------------------------------------------------------

# Background

Sensor Framework v1 đã được hoàn thiện và review.

Sprint S1 **không chỉ nhằm thêm Ultrasonic**, mà quan trọng hơn là
**kiểm chứng khả năng mở rộng của Sensor Framework** bằng một loại cảm
biến hoàn toàn khác với TCRT5000.

Nếu framework cần sửa lớn để thêm Ultrasonic thì kiến trúc hiện tại vẫn
chưa đủ tốt.

------------------------------------------------------------------------

# Goal

Tích hợp HC-SR04 (Ultrasonic) vào Sensor Framework mà:

-   Không thay đổi ISensor.
-   Không phá vỡ DigitalSensor.
-   Không sửa RobotAPI hiện có.
-   Chỉ mở rộng framework bằng các lớp mới.

------------------------------------------------------------------------

# Scope

## Task 1 -- Design DistanceSensor

Thiết kế lớp trung gian:

``` text
ISensor
    ↓
DistanceSensor
    ↓
Ultrasonic
```

DistanceSensor chịu trách nhiệm định nghĩa API chung cho mọi cảm biến đo
khoảng cách.

Ví dụ:

-   distance()
-   unit()
-   maxRange()

------------------------------------------------------------------------

## Task 2 -- Implement Ultrasonic Driver

Tạo driver độc lập:

-   Ultrasonic.h
-   Ultrasonic.cpp

Driver chỉ giao tiếp với HAL/GPIO.

Không phụ thuộc RobotAPI, VM hoặc Application.

------------------------------------------------------------------------

## Task 3 -- Sensor Framework Integration

Đăng ký Ultrasonic vào SensorManager.

Đảm bảo lifecycle:

-   Register
-   Initialize
-   Update
-   Shutdown

hoạt động đúng.

------------------------------------------------------------------------

## Task 4 -- RobotAPI Integration

Expose semantic API:

``` cpp
float distanceFront();
```

Không expose trigger/echo pin.

------------------------------------------------------------------------

## Task 5 -- VM Binding

Expose sang Python:

``` python
robot.distance_front()
```

VM không biết chi tiết phần cứng.

------------------------------------------------------------------------

## Task 6 -- Validation Programs

Viết chương trình kiểm thử:

1.  In khoảng cách liên tục.
2.  Dừng khi vật cản \< ngưỡng.
3.  Điều khiển LED theo khoảng cách.

Không cần obstacle avoidance hoàn chỉnh.

------------------------------------------------------------------------

## Task 7 -- Architecture Validation

Đánh giá lại Sensor Framework:

-   Có phải sửa ISensor không?
-   Có phải sửa DigitalSensor không?
-   Có phải sửa SensorManager không?

Nếu có, giải thích nguyên nhân và đề xuất cải tiến.

------------------------------------------------------------------------

# Deliverables

## Source

    Sensor/
    ├── DistanceSensor.h
    ├── DistanceSensor.cpp
    ├── Ultrasonic.h
    ├── Ultrasonic.cpp

## Documentation

Tạo:

-   ULTRASONIC_DRIVER_SPEC.md
-   DISTANCE_SENSOR_DESIGN.md
-   SENSOR_FRAMEWORK_VALIDATION.md

------------------------------------------------------------------------

# Acceptance Criteria

-   Ultrasonic hoạt động ổn định.
-   Không sửa kiến trúc lõi của Sensor Framework.
-   RobotAPI chỉ dùng semantic API.
-   VM đọc được khoảng cách.
-   Có tài liệu đánh giá khả năng mở rộng của framework.

------------------------------------------------------------------------

# Constraints

-   Không thêm logic tránh vật cản phức tạp.
-   Không thay đổi public API của các sensor đã hoàn thành nếu không có
    lý do kiến trúc rõ ràng.
-   Ưu tiên kiểm chứng kiến trúc hơn tối ưu hiệu năng.

------------------------------------------------------------------------

# Merge Policy

Không merge trực tiếp.

Sau khi hoàn thành, gửi:

1.  Architecture Validation Report
2.  Class Diagram cập nhật
3.  Dependency Diagram
4.  API Summary
5.  Lessons Learned khi tích hợp Ultrasonic

Chỉ merge sau khi hoàn thành Architecture Review.
