# VM ABI

## Robot Virtual Machine Application Binary Interface

Version: Foundation v1 (Frozen)

---

# 1. Purpose

Tài liệu này định nghĩa giao diện nhị phân (ABI) giữa chương trình bytecode
và Robot VM. Mọi instruction đều được mô tả chi tiết về opcode, các tham số
và hành vi.

ABI này là **hợp đồng cố định** sau Sprint 14.5. Các phiên bản tương lai
chỉ được mở rộng, không thay đổi ngữ nghĩa hiện có.

---

# 2. Instruction Format

Mỗi instruction có kích thước cố định:

```c
struct Instruction
{
    Opcode opcode;  // 1 byte (enum class)
    int16_t p1;     // 2 bytes
    int16_t p2;     // 2 bytes
    int16_t p3;     // 2 bytes
};


# 7. Error Handling

VM có thể dừng với các mã lỗi sau:

| Error Code | Ý nghĩa                          |
|------------|----------------------------------|
| 0          | Không lỗi                        |
| 1          | Opcode không hợp lệ              |
| 2          | Program counter vượt quá giới hạn (program overflow) |
| 3          | Jump target không hợp lệ (vượt quá kích thước chương trình) |

Khi gặp lỗi, VM đặt `mRunning = false` và ghi mã lỗi vào `mErrorCode`.

---

# 8. Stability Guarantee

- Opcode ID và ngữ nghĩa không thay đổi sau Sprint 14.6.
- Có thể thêm opcode mới với ID > 26.
- Có thể mở rộng `VMContext` nhưng không thay đổi các trường hiện có.
- `Instruction` layout không thay đổi.
- Error codes là hợp đồng cố định (0–3).

---

# 9. Version

ABI Version: 1.0