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