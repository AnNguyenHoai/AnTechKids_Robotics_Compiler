# Robot Language Specification

## Overview
Robot Language là ngôn ngữ lập trình dành cho robot, được thiết kế để biên dịch thành bytecode và chạy trên Robot VM.

## Syntax

### Variables
Gán biến: `speed = 80`

### Functions
Định nghĩa:
def add(a, b):
return a + b

text
Gọi: `add(3, 4)`

### Scope
- Biến toàn cục: định nghĩa ở ngoài hàm.
- Biến cục bộ: định nghĩa bên trong hàm.
- Shadowing: biến cục bộ che khuất biến toàn cục cùng tên.

### Return
`return expr` để trả về giá trị.