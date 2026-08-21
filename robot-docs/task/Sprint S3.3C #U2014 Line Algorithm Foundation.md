# Sprint S3.3C — Line Algorithm Foundation

**Sprint:** S3.3C  
**Priority:** CRITICAL  
**Owner:** DeepSeek  
**Architecture Owner:** ChatGPT

---

# 1. Objective

Xây dựng tầng Line Algorithm đầu tiên trên nền Query Transport đã hoàn thiện.

Quan trọng:

Sprint này KHÔNG được đọc GPIO.

Toàn bộ thuật toán chỉ sử dụng:

```
GetTraceV2I2CData()

GetTraceV2I2C()

GetTraceV2I2CState()

GetTraceV2I2CChxState()
```

Điều này đảm bảo thuật toán hoàn toàn độc lập với phần cứng.

---

# 2. Architecture

Tuyệt đối tuân thủ:

```
                Line Algorithm
                      │
        ┌─────────────┼─────────────┐
        │             │             │
 GetTraceRaw   GetTraceState   GetTraceValue
        │             │             │
        └─────────────┴─────────────┘
                      │
                 RobotAPI
                      │
                 SensorManager
                      │
                  TCRT5000 HAL
```

Line Algorithm KHÔNG được gọi:

```
digitalRead()

pinMode()

GPIO

HAL
```

---

# 3. APIs

Hoàn thiện:

```
line_basis(speed)

line_stop()

line_follow(speed)
```

Chưa làm:

```
line_turn()

intersection

PID

curve
```

---

# 4. line_basis()

Đây là primitive đầu tiên.

Input

```
speed
```

Thuật toán

```
mask = GetTraceV2I2CData()
```

Ví dụ

```
010

↓

Forward
```

```
100

↓

Turn Left
```

```
001

↓

Turn Right
```

```
000

↓

Stop
```

```
111

↓

Stop
```

Chỉ implement rule-based.

Không PID.

---

# 5. line_follow()

Wrapper.

```
while line exists

↓

line_basis()
```

Không thread.

Không scheduler.

---

# 6. line_stop()

Dừng motor.

Không query sensor.

---

# 7. Query Usage

Một vòng loop chỉ được phép:

```
mask = GetTraceRaw()

↓

reuse mask
```

KHÔNG được:

```
GetTraceRaw()

GetTraceState()

GetTraceValue()

GetTraceRaw()
```

liên tục trong cùng một iteration.

Nếu cần nhiều thông tin:

```
read once

↓

cache local

↓

reuse
```

---

# 8. SensorManager

Không sửa kiến trúc.

Không thêm update.

Không rewrite.

---

# 9. Motor

Chỉ sử dụng RobotAPI.

Ví dụ

```
setMotorsDirect()

forward()

stop()
```

Không đụng PWM.

---

# 10. Test

Tạo

```
examples/

physical/

019_line_basis.py
```

Ví dụ

```python
import rcu

while True:

    rcu.line_basis(60)
```

---

Tạo

```
020_line_follow.py
```

Ví dụ

```python
import rcu

rcu.line_follow(60)
```

---

# 11. Regression

PASS

Motion

LED

MP3

Wait

Thread

Light

Patrol

Compiler

Frontend

Integration

---

# 12. Documentation

Tạo

```
robot-docs/

S3_3C_LINE_ALGORITHM.md
```

Bao gồm

- Architecture
- State Machine
- Mask Mapping
- Decision Table
- RobotAPI Flow
- Test
- Limitation

---

# 13. Decision Table

Document rõ:

| Mask | Action |
|------|--------|
|010|Forward|
|100|Turn Left|
|001|Turn Right|
|000|Stop|
|111|Stop|

Không hardcode ở nhiều nơi.

---

# 14. Important

Không implement

```
PID

intersection

curve

calibration

speed control

adaptive threshold
```

Sprint này chỉ tạo primitive.

---

# 15. Acceptance

- [ ] line_basis REAL
- [ ] line_follow REAL
- [ ] line_stop REAL
- [ ] Không đọc GPIO
- [ ] Chỉ dùng Query API
- [ ] Một iteration chỉ đọc Query một lần
- [ ] Physical board PASS
- [ ] Regression PASS
- [ ] Documentation PASS

STOP.

Không làm intersection.

Không làm PID.

Chờ Architecture Review.