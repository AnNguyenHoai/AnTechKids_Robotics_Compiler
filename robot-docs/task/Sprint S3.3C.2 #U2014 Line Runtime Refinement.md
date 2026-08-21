# Sprint S3.3C.2 — Line Runtime Refinement

**Sprint:** S3.3C.2  
**Priority:** CRITICAL  
**Owner:** DeepSeek  
**Architecture Owner:** ChatGPT

---

# 1. Objective

Đây là sprint cuối cùng của Line Foundation.

Không thêm feature.

Không thêm API.

Không thêm thuật toán.

Chỉ sửa Runtime Architecture.

Sau sprint này:

- Line runtime trở thành non-blocking.
- Một iteration chỉ đọc sensor một lần.
- Kiến trúc đủ ổn định để phát triển PID, Intersection và Behavior.

---

# 2. Review Findings

Architecture Review phát hiện hai blocker:

## Blocker 1

```
LineFollow()

↓

while(true)
```

=> Block runtime.

Không phù hợp với:

- VM
- Scheduler
- Behavior
- Multi-thread
- Future Event Loop

---

## Blocker 2

Một iteration:

```
GetTraceRaw()

↓

LineBasis()

↓

GetTraceRaw()
```

Sensor bị đọc nhiều lần.

Vi phạm contract:

```
Read Once

Reuse Everywhere
```

---

# 3. Runtime Contract

Từ sprint này:

```
LineFollow()

↓

One Tick

↓

Return
```

KHÔNG được:

```
while

delay

sleep

loop forever
```

Runtime scheduler sẽ gọi lại.

---

# 4. New Execution Model

Thay:

```
while(true)

↓

LineBasis()

↓

delay(10)
```

bằng:

```
tick

↓

LineFollow()

↓

return
```

Không block.

---

# 5. LineContext

Tạo context.

Ví dụ

```cpp
struct LineContext
{
    uint8_t mask;

    LineState state;

    MotorCommand command;
};
```

LineContext chỉ tồn tại trong một iteration.

Không global.

---

# 6. One Read Policy

Một iteration:

```
mask

↓

Perception

↓

Decision

↓

Motion
```

KHÔNG:

```
mask

↓

throw away

↓

GetTraceRaw()

↓

throw away
```

---

# 7. LineBasis()

Sửa signature.

Ví dụ

```cpp
void LineBasis(
    const LineContext&
);
```

hoặc

```cpp
void LineBasis(
    uint8_t mask
);
```

Miễn sao:

```
Không đọc sensor lần thứ hai.
```

---

# 8. LineFollow()

LineFollow chỉ làm:

```
Read Sensor

↓

Create Context

↓

LineBasis(Context)

↓

Return
```

Không while.

Không delay.

---

# 9. Decision Layer

Không sửa behavior.

Chỉ đổi input.

Hiện

```
mask

↓

Decision
```

Đổi thành

```
Context

↓

Decision
```

Nếu thuận tiện.

Không bắt buộc.

---

# 10. Motion

Không thay đổi.

Không sửa RobotAPI.

Không sửa Motor.

---

# 11. Physical Tests

Update:

```
019_line_basis.py
```

```
020_line_follow.py
```

Không dùng:

```
_thread
```

Không block.

Ví dụ

```python
while True:

    rcu.line_follow(70)

    rcu.SetWaitForTime(0.02)
```

---

# 12. Documentation

Update architecture.

Execution model phải thể hiện:

```
Tick

↓

Context

↓

Perception

↓

Decision

↓

Motion

↓

Return
```

Không còn:

```
while(true)
```

---

# 13. Regression

PASS

- Motion
- Wait
- LED
- MP3
- Thread
- Query
- LineBasis
- Compiler
- Frontend
- Integration

Không thay đổi behavior.

---

# 14. Code Hygiene

Dọn:

- duplicate include
- comment cũ
- obsolete description

Không refactor lớn.

---

# 15. Acceptance Criteria

- [ ] LineFollow() non-blocking.
- [ ] Không còn while nội bộ.
- [ ] Không còn delay trong runtime.
- [ ] Một iteration chỉ đọc sensor một lần.
- [ ] Có LineContext.
- [ ] LineBasis() reuse dữ liệu đã đọc.
- [ ] Physical examples cập nhật.
- [ ] Documentation đồng bộ.
- [ ] Regression PASS.

STOP.

Không làm PID.

Không làm Intersection.

Không làm Curve.

Không làm Calibration.

Chờ Architecture Review.