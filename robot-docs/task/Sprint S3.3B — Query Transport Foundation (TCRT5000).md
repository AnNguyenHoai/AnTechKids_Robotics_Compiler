# Sprint S3.3B — Query Transport Foundation (TCRT5000)

**Sprint:** S3.3B  
**Priority:** Critical  
**Owner:** DeepSeek  
**Reviewer:** ChatGPT

---

# 1. Objective

Hoàn thiện toàn bộ Query Transport layer để RoboSim có thể đọc dữ liệu từ TCRT5000 trên robot thật.

Đây là sprint cuối cùng của tầng Sensor Query.

Sau sprint này:

```
RoboSim

↓

Compiler

↓

VM

↓

RobotAPI

↓

TCRT5000 HAL
```

hoạt động end-to-end.

---

# 2. Architecture

## KHÔNG tạo driver mới.

Toàn bộ Query API phải sử dụng đúng driver:

```
TCRT5000 HAL
```

đã tồn tại.

Không duplicate logic.

Không tạo:

```
PatrolSensor

LineSensor

TraceSensor
```

Driver duy nhất là:

```
TCRT5000
```

LightSensor và Patrol chỉ là hai abstraction khác nhau.

---

# 3. APIs cần hoàn thiện

## REAL

### GetTraceV2I2C()

```
int GetTraceV2I2C(
    int port,
    int channel
)
```

Return:

```
0

50

100

...
```

Mapping sử dụng trực tiếp dữ liệu của TCRT5000 HAL.

---

### GetTraceV2I2CState()

```
bool GetTraceV2I2CState(
    int port,
    int channel
)
```

Return bool.

Không đọc GPIO trực tiếp.

---

### GetTraceV2I2CChxState()

```
bool GetTraceV2I2CChxState(
    int port,
    int channel
)
```

Return bool.

---

### GetTraceV2I2CData()

```
int GetTraceV2I2CData(
    int port
)
```

Return raw bitmask.

Ví dụ

```
001

010

111
```

Không convert.

---

# 4. Adapter

Adapter phải support:

```
rcu.GetTraceV2I2C()

↓

get_trace_value()
```

```
rcu.GetTraceV2I2CState()

↓

get_trace_state()
```

```
rcu.GetTraceV2I2CChxState()

↓

get_trace_ch_state()
```

```
rcu.GetTraceV2I2CData()

↓

get_trace_raw()
```

---

# 5. Compiler

Compiler support:

- literal argument
- variable argument

Không duplicate opcode.

Không renumber opcode.

---

# 6. VM

VM dispatch đầy đủ.

Không implement logic tại VM.

VM chỉ forward RobotAPI.

---

# 7. RobotAPI

RobotAPI chỉ đọc từ:

```
TCRT5000 HAL
```

Không đọc GPIO.

Không tạo cache riêng.

Không duplicate.

---

# 8. HAL

HAL là single source of truth.

Tất cả API đều đọc từ:

```
readMask()

readCenter()

readDigital()

...
```

(nếu đã có)

Nếu thiếu helper nhỏ thì được phép bổ sung.

Không rewrite HAL.

---

# 9. Tests

Tạo

```
examples/
    physical/
        018_trace_query.py
```

Test

```
while True:

    print(
        rcu.GetTraceV2I2CData(1)
    )
```

---

```
while True:

    print(
        rcu.GetTraceV2I2C(1,1)
    )
```

---

```
while True:

    if rcu.GetTraceV2I2CState(1,1):

        rcu.Set3CLed(1,1)

    else:

        rcu.Set3CLed(1,0)
```

---

```
while True:

    if rcu.GetTraceV2I2CChxState(1,1):

        rcu.SetMp3Play(1)
```

(Nếu buzzer module chưa hoạt động thì chỉ cần log.)

---

# 10. Regression

PASS toàn bộ:

```
frontend

compiler

integration

physical compile
```

Không được làm hỏng:

Motion

LED

MP3

Wait

Thread

LightSensor

---

# 11. Documentation

Tạo

```
robot-docs/

S3_3B_QUERY_TRANSPORT.md
```

Bao gồm

- Architecture
- Adapter
- Compiler
- VM
- RobotAPI
- HAL
- Test
- Mapping

---

# 12. Important

Không implement:

```
line_basis()

line_turn()

line_follow()

intersection

PID
```

Sprint này chỉ hoàn thiện Query Transport.

---

# 13. Acceptance Criteria

- [ ] GetTraceV2I2C REAL
- [ ] GetTraceV2I2CState REAL
- [ ] GetTraceV2I2CChxState REAL
- [ ] GetTraceV2I2CData REAL
- [ ] Adapter PASS
- [ ] Compiler PASS
- [ ] VM PASS
- [ ] RobotAPI PASS
- [ ] HAL reuse PASS
- [ ] Physical board PASS
- [ ] Documentation PASS

STOP.

Không làm tiếp Line Algorithm.

Chờ Architecture Review.