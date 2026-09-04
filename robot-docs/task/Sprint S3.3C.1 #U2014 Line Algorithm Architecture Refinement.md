# Sprint S3.3C.1 — Line Algorithm Architecture Refinement

**Sprint:** S3.3C.1  
**Priority:** HIGH  
**Owner:** DeepSeek  
**Architecture Owner:** ChatGPT

---

# 1. Objective

Refactor Line Algorithm architecture.

Không thêm feature mới.

Không thêm API mới.

Không thêm thuật toán mới.

Mục tiêu duy nhất:

> Chuẩn bị kiến trúc cho PID, Intersection và Multi-Sensor trong các sprint tiếp theo.

---

# 2. Current Problems

Qua Architecture Review phát hiện các vấn đề:

## Problem 1

line_follow()

↓

internal while()

↓

block execution

↓

không phù hợp với RoboSim runtime.

---

## Problem 2

Decision logic

↓

nằm trong line_basis()

↓

khó mở rộng.

---

## Problem 3

Mask

↓

Motor

↓

coupling quá chặt.

---

## Problem 4

Physical test sử dụng _thread.

Không cần thiết.

---

## Problem 5

Board status/document chưa đồng nhất.

---

# 3. New Architecture

Thay đổi kiến trúc thành:

```
               Query Layer
                    │
                    ▼
            Perception Layer
                    │
                    ▼
             Decision Layer
                    │
                    ▼
              Motion Layer
                    │
                    ▼
                RobotAPI
```

---

# 4. Perception Layer

Tạo module mới.

Ví dụ

```
LinePerception
```

Không đọc GPIO.

Không điều khiển motor.

Chỉ convert

```
Bitmask

↓

LineState
```

Ví dụ

```
000

↓

LOST
```

```
010

↓

CENTER
```

```
100

↓

LEFT
```

```
001

↓

RIGHT
```

```
111

↓

INTERSECTION
```

Không thêm thuật toán.

---

# 5. LineState

Tạo enum.

Ví dụ

```cpp
enum class LineState
{
    LOST,

    CENTER,

    LEFT,

    RIGHT,

    INTERSECTION,

    UNKNOWN
};
```

Toàn bộ tầng trên chỉ sử dụng:

```
LineState
```

Không sử dụng bitmask.

---

# 6. Decision Layer

Tạo module riêng.

Ví dụ

```
LineDecisionEngine
```

Input

```
LineState
```

Output

```
MotorCommand
```

Ví dụ

```
CENTER

↓

FORWARD
```

```
LEFT

↓

TURN_LEFT
```

```
RIGHT

↓

TURN_RIGHT
```

```
LOST

↓

STOP
```

```
INTERSECTION

↓

STOP
```

Không điều khiển motor.

---

# 7. Motion Layer

line_basis()

↓

chỉ làm:

```
Decision

↓

RobotAPI
```

Không chứa:

if(mask...)

switch(mask...)

bit operation

---

# 8. line_follow()

Sửa semantics.

Không được:

```
while(...)
```

Không block.

Một lần gọi:

```
Read

↓

Perception

↓

Decision

↓

Motor

↓

Return
```

Behavior Scheduler sẽ gọi lại.

VM cũng gọi lại.

Không tự loop.

---

# 9. Physical Tests

Loại bỏ

```
_thread
```

Tất cả test đổi thành:

```python
while True:

    rcu.line_basis(60)

    rcu.SetWaitForTime(0.05)
```

Hoặc

```python
while True:

    rcu.line_follow(60)

    rcu.SetWaitForTime(0.05)
```

Không dùng thread.

---

# 10. Documentation

Sửa toàn bộ document.

Architecture mới phải thể hiện:

```
Query

↓

Perception

↓

Decision

↓

Motion

↓

RobotAPI
```

Không còn:

```
Mask

↓

Motor
```

---

# 11. Opcode

Review lại.

Nếu

```
4096
```

chỉ là symbolic value.

Document rõ.

Nếu là opcode thật.

Sửa theo opcode system hiện tại.

Không tạo opcode namespace riêng.

---

# 12. Board Validation

Document phải phản ánh đúng trạng thái.

Nếu chưa nghiệm thu.

```
Pending
```

Không đánh dấu PASS.

---

# 13. Regression

PASS

- Motion
- Wait
- LED
- MP3
- Thread
- Light
- Patrol Query
- Line Basis

Không thay đổi behavior.

Chỉ thay đổi architecture.

---

# 14. Acceptance Criteria

- [ ] line_follow() không block.
- [ ] Không còn while nội bộ.
- [ ] Có LineState.
- [ ] Có Perception Layer.
- [ ] Có Decision Layer.
- [ ] line_basis() không còn xử lý bitmask trực tiếp.
- [ ] Không dùng _thread trong physical tests.
- [ ] Opcode được chuẩn hóa.
- [ ] Documentation đồng nhất.
- [ ] Regression PASS.

STOP.

Không implement PID.

Không implement Intersection.

Không implement Curve.

Chờ Architecture Review.