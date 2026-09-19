# EPIC H31 — Boolean Expression Completeness

## 1. Mục tiêu

H31 hoàn thiện semantics biểu thức Boolean của RoboSim Python trên compiler hiện tại mà không thay đổi ISA/bytecode và không thêm opcode mới.

Phạm vi chính:

- hỗ trợ đầy đủ `and`
- hỗ trợ đầy đủ `or`
- hỗ trợ `not`
- hỗ trợ lồng `and` / `or` / `not`
- hỗ trợ Boolean expression trong assignment, `if`, `while` và Robot API argument
- giữ short-circuit đúng thứ tự từ trái sang phải
- giữ truthiness thống nhất với VM: `0` là False, khác `0` là True

## 2. Quyết định semantics

### 2.1 Boolean result được chuẩn hóa

RoboSim Boolean expression trả kết quả canonical:

- False -> `0`
- True -> `1`

Ví dụ:

```python
result = 7 and 3
```

RoboSim trả `1`, không trả `3` như CPython.

Lý do:

- đây là behavior đã tồn tại của `and` trước H31
- VM comparison cũng đã trả `0/1`
- giữ một Boolean contract đơn giản, xác định và phù hợp với robot VM
- tránh thay đổi ngầm semantics bytecode cũ

### 2.2 Truthiness

VM hiện tại kiểm tra:

- `0` -> False
- giá trị khác `0` -> True

H31 dùng đúng contract này cho `and`, `or`, `not`.

## 3. Lowering strategy

H31 không thêm opcode Boolean mới.

Sử dụng opcode canonical hiện có:

- `JumpIfFalse`
- `JumpIfTrue`
- `Jump`
- `LoadConst`

### 3.1 AND

Mỗi operand được evaluate từ trái sang phải.

- gặp operand False -> nhảy tới false branch ngay
- không evaluate các operand phía sau
- nếu tất cả True -> result = `1`

### 3.2 OR

Mỗi operand được evaluate từ trái sang phải.

- gặp operand True -> nhảy tới true branch ngay
- không evaluate các operand phía sau
- nếu tất cả False -> result = `0`

### 3.3 NOT

Operand được evaluate đúng một lần.

- operand False -> result = `1`
- operand True -> result = `0`

## 4. Nested expression correctness

Trước H31, `BoolHandler` gọi `compiler.visit(expr)` cho operand của `and`.

Điều này chỉ ổn với một số AST node có visitor trả value trực tiếp, ví dụ comparison. Các operand dạng arithmetic, unary, call hoặc Boolean expression phức tạp có thể không đi qua canonical expression path.

H31 đổi toàn bộ Boolean operand sang:

```python
compiler.compile_expression(expr)
```

Nhờ đó cùng một expression contract được dùng ở mọi mức nesting.

Ví dụ được hỗ trợ:

```python
result = (1 + 1) and (3 - 2)
result = a or (b and not c)
result = not ((a and b) or c)
```

## 5. Precedence

H31 không tự định nghĩa parser precedence mới.

Compiler nhận Python AST nên giữ precedence chuẩn của parser:

1. `not`
2. `and`
3. `or`

Ví dụ:

```python
not a or b and c
```

được hiểu là:

```python
(not a) or (b and c)
```

## 6. Short-circuit safety

Short-circuit là requirement bắt buộc, không chỉ optimization.

Ví dụ:

```python
result = 0 and (1 / 0)
result = 1 or (1 / 0)
```

Cả hai phải chạy an toàn vì operand `1 / 0` không được execute.

H31 test trực tiếp behavior này ở compiler control flow và Python VM end-to-end.

## 7. Không thay đổi trong H31

H31 không mở rộng:

- chained comparison như `a < b < c`
- unary plus `+x`
- Python value-propagating semantics của `and/or`
- ternary expression
- list/dict/set truthiness
- object truthiness

Chained comparison tiếp tục fail closed theo H29-C.

## 8. Acceptance matrix

H31 gate phải cover tối thiểu:

- truth table `and`
- truth table `or`
- `not` với zero/non-zero
- normalized result `0/1`
- double `not`
- nested `and/or/not`
- arithmetic operand trong Boolean expression
- operator precedence
- assignment context
- `if` context
- `while` context
- Robot API argument context
- `and` short-circuit
- `or` short-circuit
- canonical `JumpIfTrue` / `JumpIfFalse`
- H29-C chained-comparison rejection vẫn giữ
- toàn bộ repository regression vẫn PASS

## 9. Kiến trúc

H31 chỉ thay đổi compiler lowering và regression contract.

Không thay đổi:

- opcode numbering
- bytecode schema
- VM wire contract
- ESP32 runtime behavior
- capability contract
- deployment contract

Điều này giữ H31 backward-compatible ở ISA/runtime boundary.
