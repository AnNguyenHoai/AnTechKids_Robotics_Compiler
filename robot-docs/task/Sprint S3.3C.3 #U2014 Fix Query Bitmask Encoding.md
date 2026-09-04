# Sprint S3.3C.3 — Fix Query Bitmask Encoding

**Sprint:** S3.3C.3  
**Priority:** CRITICAL (Architecture Bug)  
**Owner:** DeepSeek  
**Architecture Owner:** ChatGPT

---

# 1. Background

Qua physical board validation phát hiện Line Algorithm hoạt động sai.

Ví dụ:

```
Che sensor Left
↓

Robot không rẽ trái
```

```
Che sensor Right
↓

Robot lại rẽ trái
```

Ban đầu nghi ngờ:

- Decision Layer
- Motion Layer

Sau khi kiểm tra bằng physical test, xác định nguyên nhân KHÔNG nằm ở thuật toán.

---

# 2. Root Cause

Physical validation:

| Physical Sensor | GetTraceV2I2CData() |
|-----------------|---------------------|
| Left            | 001                 |
| Center          | 010                 |
| Right           | 100                 |

Trong khi toàn bộ kiến trúc đã thống nhất:

```
Bit2 = LEFT

Bit1 = CENTER

Bit0 = RIGHT
```

Hiện tại implementation đang encode:

```
Bit2 = RIGHT

Bit1 = CENTER

Bit0 = LEFT
```

Đây là lỗi Query Encoding.

Không phải lỗi Decision.

Không phải lỗi Line Algorithm.

---

# 3. Objective

Chuẩn hóa toàn bộ Query Layer.

Sau sprint này:

| Physical Sensor | Bit |
|-----------------|-----|
| Left            |100|
| Center          |010|
| Right           |001|

Đây là quy ước CHÍNH THỨC của dự án.

Architecture Freeze.

---

# 4. Scope

Chỉ được sửa:

- TCRT5000 HAL
- Query Encoding
- Mapping

KHÔNG sửa:

- Perception Layer
- Decision Layer
- Motion Layer
- LineBasis
- LineFollow
- PID

---

# 5. Required Changes

Review toàn bộ quá trình tạo bitmask.

Ví dụ nếu hiện tại:

```cpp
mask =
(right << 2) |
(center << 1) |
(left);
```

đổi thành:

```cpp
mask =
(left << 2) |
(center << 1) |
(right);
```

Nếu lỗi nằm ở GPIO mapping:

Ví dụ

```cpp
left = sensor[2];
right = sensor[0];
```

thì sửa mapping.

Không workaround ở tầng trên.

---

# 6. Validation

Tạo physical validation.

## Test 1

```python
while True:

    if rcu.GetTraceV2I2CData(1)==4:

        rcu.Set3CLed(1,1)

    else:

        rcu.Set3CLed(1,0)

    rcu.SetWaitForTime(0.05)
```

Expected:

```
Che Left

↓

LED ON
```

---

## Test 2

```
==2
```

Expected:

```
Che Center

↓

LED ON
```

---

## Test 3

```
==1
```

Expected:

```
Che Right

↓

LED ON
```

---

# 7. Regression

Sau khi sửa phải test lại:

```
line_follow()
```

Expected:

| Sensor detect | Robot Action |
|---------------|--------------|
|Left|Turn Left|
|Center|Forward|
|Right|Turn Right|

Không sửa Decision Engine.

Nếu behavior sai sau khi bitmask đúng mới tiếp tục review.

---

# 8. Documentation

Cập nhật:

```
robot-docs/

S3_3C_QUERY_ENCODING.md
```

Bao gồm:

## Official Bit Mapping

```
Bit2 = Left

Bit1 = Center

Bit0 = Right
```

Giải thích đây là Architecture Contract.

Không được thay đổi ở các sprint sau.

---

# 9. Acceptance Criteria

- [ ] Bit2 = Left
- [ ] Bit1 = Center
- [ ] Bit0 = Right
- [ ] Physical validation PASS
- [ ] line_follow() PASS
- [ ] Không sửa Decision Layer
- [ ] Không sửa Motion Layer
- [ ] Regression PASS
- [ ] Documentation cập nhật

STOP.

Không phát triển feature mới.

Đây là bug-fix sprint.