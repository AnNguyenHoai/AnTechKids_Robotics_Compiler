# RoboStudio – MVP

RoboStudio là một công cụ GUI đơn giản giúp học sinh biên dịch chương trình RoboSim mà không cần sử dụng Command Prompt.

## Yêu cầu

- Python 3.8+
- PySide6
- Robot CLI (có thể cài từ `robot-cli/`)
- Robot Platform đã được clone và có file firmware `robot-platform/main/main.ino`

## Cài đặt Robot CLI

```bash
cd robot-cli
pip install -e .

cd robostudio
python main.py


---

## Cách hoạt động

- `FirmwareService` tự động tìm `robot-platform/main/main.ino` hoặc `robot-platform/RobotVM.ino` trong cùng workspace.
- Nếu file tồn tại, nó sẽ được mở bằng ứng dụng mặc định (Arduino IDE).
- Người dùng không cần phải chỉnh sửa config cho đường dẫn firmware.

---

## Kết luận

Với thay đổi này, RoboStudio hoàn toàn không cần cấu hình đường dẫn firmware. Nó sẽ tự động tìm `main.ino` hoặc `RobotVM.ino` dựa trên vị trí của repository. Điều này giúp trải nghiệm người dùng liền mạch hơn, đặc biệt khi di chuyển thư mục.

**Sprint M4.1 coi như hoàn tất.** Bạn có thể tiến hành Architecture Review và chuẩn bị cho M4.2 nếu cần.