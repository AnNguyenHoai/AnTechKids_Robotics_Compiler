# Behavior Lifecycle

## States
- **CREATED**: Behavior mới được tạo, chưa khởi tạo.
- **INITIALIZED**: Đã gọi init() nhưng chưa start().
- **RUNNING**: Đang thực thi.
- **COMPLETED**: Hoàn thành thành công.
- **FAILED**: Thất bại.
- **INTERRUPTED**: Bị dừng giữa chừng.
- **CANCELLED**: Bị hủy bởi scheduler.

## Methods
- `init(context)`: Khởi tạo, không block.
- `start(context)`: Bắt đầu hành động.
- `update(context)`: Được gọi liên tục trong loop để cập nhật trạng thái.
- `pause()`, `resume()`: Tạm dừng / tiếp tục.
- `stop()`: Dừng ngay lập tức.
- `reset()`: Đưa về CREATED.

## Transition Diagram
CREATED -> INITIALIZED -> RUNNING -> COMPLETED
                          -> FAILED
                          -> INTERRUPTED
                          -> CANCELLED