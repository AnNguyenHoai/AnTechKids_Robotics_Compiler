
## Mục đích

Hai động cơ trên robot thường có tốc độ thực tế khác nhau dù cùng nhận PWM như nhau.  
Việc hiệu chỉnh cho phép bù sai lệch này để robot đi thẳng khi nhận lệnh `forward(50)`.

## Mô hình hiệu chỉnh

Tốc độ hiệu quả của mỗi động cơ được tính:
effectiveLeft = commandLeft × speedScale × leftMotorScale
effectiveRight = commandRight × speedScale × rightMotorScale



Sau đó giới hạn trong khoảng [-100, 100].  
`leftMotorScale` và `rightMotorScale` là hai thông số điều chỉnh.

## Các lệnh Serial

| Lệnh | Mô tả |
|------|-------|
| `motor calib show` | Hiển thị giá trị hiện tại và ví dụ. |
| `motor calib set left <val>` | Gán hệ số cho động cơ trái (0.50 – 1.50). |
| `motor calib set right <val>` | Gán hệ số cho động cơ phải. |
| `motor calib reset` | Đặt cả hai về 1.0. |
| `motor calib test <speed>` | Chạy thử cả hai động cơ ở tốc độ yêu cầu, in ra tốc độ hiệu quả. |
| `config show` | Xem toàn bộ cấu hình, bao gồm cả ví dụ. |
| `config save` | Lưu cấu hình vào bộ nhớ (nếu được hỗ trợ). |

## Quy trình hiệu chỉnh

1. Đặt robot trên mặt phẳng, pin đầy.
2. Đặt cả hai hệ số về 1.0: `motor calib reset`
3. Chạy thử với tốc độ 50: `motor calib test 50`
4. Quan sát hướng đi:
   - Nếu robot lệch sang trái → động cơ phải chạy nhanh hơn → giảm `rightMotorScale`.
   - Nếu lệch sang phải → giảm `leftMotorScale`.
5. Điều chỉnh từng bước 0.02–0.05, chạy thử lại.
6. Kiểm tra ở nhiều tốc độ (30, 50, 70, 90).
7. Sau khi hài lòng, lưu cấu hình: `config save`

## Ví dụ

Nếu robot lệch phải (động cơ trái chạy nhanh hơn):
motor calib set left 0.92
motor calib test 50



Lúc đó, lệnh `forward(50)` sẽ cho tốc độ hiệu quả trái ~46, phải 50 → robot đi thẳng hơn.

## Lưu ý an toàn

- Không đặt hệ số quá thấp (< 0.5) hoặc quá cao (> 1.5).
- Khi thay đổi hệ số trong lúc động cơ đang chạy, tốc độ sẽ thay đổi ngay lập tức; hãy cẩn thận.
- Luôn kiểm tra với pin đầy để kết quả nhất quán.

## Lưu trữ

Cấu hình hiện tại được lưu trong RAM. Lệnh `config save` (nếu được triển khai) sẽ ghi vào bộ nhớ vĩnh viễn. Nếu chưa có, cấu hình sẽ mất sau khi reset.