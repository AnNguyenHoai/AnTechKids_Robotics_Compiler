# EPIC H30 — Multi-Robot Management

## Mục tiêu

RoboStudio phải quản lý được nhiều robot trong cùng một lớp học mà không xem kết quả của một lần `Discover` là toàn bộ trạng thái hệ thống.

H30 xây trên hai nền tảng đã có:

- H27 cung cấp identity ổn định bằng `device_id` và discovery qua LAN.
- H29 bảo đảm robot vẫn phục vụ Discovery/HTTP/OTA khi chương trình học sinh đang chạy.

H30 không làm group deployment hoặc orchestration nhiều robot đồng thời. Những nội dung đó thuộc epic sau.

## H30-A — Persistent Robot Registry

Registry dùng `device_id` làm khóa duy nhất.

Yêu cầu:

- lưu được nhiều robot qua lần đóng/mở RoboStudio;
- không tạo duplicate khi cùng robot đổi địa chỉ IP;
- lưu snapshot identity/capability/firmware gần nhất;
- lưu `selected_device_id` thay vì vị trí index trong UI;
- mutable state phải nằm dưới external RoboStudio state root, không ghi vào release directory;
- trạng thái `online` không được persist qua restart vì đó chỉ là observation tạm thời.

## H30-B — Discovery Merge

Một lần Discovery chỉ cập nhật availability hiện tại.

Quy tắc merge:

- robot được thấy trong scan hiện tại → `Online` và refresh snapshot;
- robot đã biết nhưng không xuất hiện → giữ registry record và chuyển `Offline`;
- robot mới → thêm theo `device_id`;
- nhiều packet cùng `device_id` → một record;
- IP mới của cùng `device_id` → update record hiện tại;
- selected robot vẫn được giữ ngay cả khi Offline.

## H30-C — RoboStudio Multi-Robot UX

Robot tab phải:

- hiển thị cả Online và Offline robots;
- khôi phục selected robot bằng `device_id` sau restart;
- không xóa danh sách known robots khi người dùng bấm Discover;
- chỉ enable OTA Run khi selected robot hiện đang Online, Ready và hỗ trợ OTA;
- refresh registry sau first-flash hoặc OTA verification thành công.

## First-Flash Safety trong lớp nhiều robot

USB upload không tự cung cấp mapping sang LAN `device_id`.

Vì vậy RoboStudio không được dùng `robots[0]` sau first-flash. Trước khi flash, RoboStudio snapshot các robot đang có trên LAN. Sau reboot, chỉ khi có đúng một `device_id` mới xuất hiện thì mới được auto-bind robot đó.

Nếu không có robot mới hoặc có nhiều robot mới cùng lúc, first-flash vẫn có thể thành công nhưng RoboStudio phải yêu cầu người dùng `Discover` và chọn robot theo identity.

Quy tắc này ưu tiên tránh deploy nhầm robot hơn là tự động hóa bằng suy đoán.

## Persistence schema

File mặc định:

```text
<ROBOSTUDIO_STATE_ROOT>/robots/robot_registry.json
```

Schema version: `1`

Persistent fields:

- registry type/schema;
- `selected_device_id`;
- danh sách robot identity snapshot;
- `last_seen_utc`.

Không persist:

- `online`;
- Wi-Fi password;
- OTA password;
- worker/thread state;
- transient deployment state.

## Acceptance

Automated acceptance phải chứng minh:

1. hai hoặc nhiều robot survive restart;
2. selected `device_id` survive restart;
3. restart không tự nhận robot là Online;
4. IP change không tạo duplicate;
5. discovery giữ robot Offline thay vì xóa;
6. first-flash không bind arbitrary robot;
7. Robot tab dùng registry và gate OTA bằng trạng thái Online;
8. full repository regression và Windows production ZIP build vẫn PASS.

Physical acceptance sau CI nên dùng ít nhất 2 robot thật trên cùng Wi-Fi:

- Discover cả hai;
- chọn Robot A;
- tắt Robot A và Discover lại → A Offline, B Online, selection A vẫn còn;
- bật lại A với IP có thể thay đổi → A quay lại Online nhưng vẫn cùng `device_id`;
- restart RoboStudio → cả A/B vẫn có trong registry nhưng bắt đầu Offline cho đến lần Discover mới;
- OTA chỉ được enable cho robot đang Online.
