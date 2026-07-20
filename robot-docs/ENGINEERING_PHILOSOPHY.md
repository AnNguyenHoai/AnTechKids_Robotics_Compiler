# ENGINEERING_PHILOSOPHY.md

# Robot Development Platform

## Engineering Philosophy

Version: Foundation v1 (Draft)

------------------------------------------------------------------------

# 1. Purpose

Tài liệu này mô tả triết lý thiết kế của Robot Development Platform.

Nó không giải thích cách code.

Nó giải thích **vì sao** hệ thống được thiết kế như hiện tại.

Mọi quyết định kiến trúc trong dự án nên được đối chiếu với tài liệu
này.

------------------------------------------------------------------------

# 2. Engineering Goal

Mục tiêu của dự án không phải chỉ tạo ra một Robot Compiler.

Mục tiêu là xây dựng một **Robot Development Platform** có thể phát
triển trong nhiều năm mà vẫn giữ được kiến trúc ổn định.

Ưu tiên:

1.  Khả năng mở rộng.
2.  Khả năng bảo trì.
3.  Tính độc lập giữa các thành phần.
4.  Tính nhất quán.

------------------------------------------------------------------------

# 3. Foundation Before Feature

Nguyên tắc quan trọng nhất của dự án:

> Foundation luôn quan trọng hơn Feature.

Không bổ sung tính năng mới nếu nền tảng chưa đủ ổn định.

Một nền tảng tốt sẽ giúp việc phát triển tính năng sau này nhanh và an
toàn hơn.

------------------------------------------------------------------------

# 4. Separation of Responsibility

Mỗi repository chỉ có một trách nhiệm duy nhất.

robot-language

-   Định nghĩa ngôn ngữ.

robot-frontend

-   Chuyển đổi chương trình đầu vào.

robot-compiler

-   Biên dịch.

robot-platform

-   Thực thi.

Không repository nào được đảm nhận nhiều vai trò.

------------------------------------------------------------------------

# 5. Single Source of Truth

Mọi định nghĩa về Robot Language chỉ tồn tại ở một nơi.

    api.yaml

Không sao chép Specification.

Không tạo nhiều nguồn dữ liệu giống nhau.

Mọi Artifact đều được sinh từ Specification.

------------------------------------------------------------------------

# 6. Artifact Driven Development

Repository không giao tiếp trực tiếp với nhau.

Chúng giao tiếp thông qua Artifact.

    Specification

    ↓

    Artifact

    ↓

    Consumer

Điều này giúp giảm phụ thuộc và tăng khả năng mở rộng.

------------------------------------------------------------------------

# 7. Frontend Independence

Frontend chỉ là nơi tạo ra chương trình.

Frontend không được ảnh hưởng tới Compiler hoặc Runtime.

Một Frontend mới có thể được bổ sung mà không cần thay đổi Compiler.

------------------------------------------------------------------------

# 8. Hardware Independence

Compiler không biết Robot Hardware.

Runtime là lớp duy nhất giao tiếp với RobotAPI.

Điều này cho phép thay đổi phần cứng mà không cần thay đổi Compiler.

------------------------------------------------------------------------

# 9. Layered Architecture

Mỗi Layer chỉ biết Layer ngay bên dưới.

    Application

    ↓

    Frontend

    ↓

    Language

    ↓

    Compiler

    ↓

    Runtime

    ↓

    Hardware

Không được bỏ qua Layer.

------------------------------------------------------------------------

# 10. Generated Code Philosophy

Generated File không phải nơi để chỉnh sửa.

Nếu muốn thay đổi Generated File thì phải thay đổi:

-   Specification
-   Generator

Không sửa trực tiếp kết quả sinh ra.

------------------------------------------------------------------------

# 11. Stable Interfaces

Interface phải ổn định.

Implementation có thể thay đổi.

Nếu cần thay đổi Interface thì phải cân nhắc ảnh hưởng tới toàn bộ
Platform.

------------------------------------------------------------------------

# 12. Small Changes

Một thay đổi nhỏ tốt hơn một thay đổi lớn.

Một Commit chỉ nên giải quyết một vấn đề.

Điều này giúp:

-   Review dễ hơn.
-   Regression dễ hơn.
-   Khôi phục dễ hơn.

------------------------------------------------------------------------

# 13. Regression First

Mỗi thay đổi đều phải có Regression.

Không xem việc build thành công là đủ.

Hệ thống phải hoạt động đúng sau khi thay đổi.

------------------------------------------------------------------------

# 14. Documentation Is Part of the Product

Tài liệu là một phần của sản phẩm.

Một tính năng chỉ được xem là hoàn thành khi:

-   Code hoàn thành.
-   Test hoàn thành.
-   Documentation được cập nhật.

------------------------------------------------------------------------

# 15. Long-Term Thinking

Mọi quyết định nên ưu tiên lợi ích dài hạn.

Không tối ưu cho tốc độ phát triển ngắn hạn nếu điều đó làm giảm chất
lượng kiến trúc.

------------------------------------------------------------------------

# 16. Engineering Values

Khi có nhiều phương án, ưu tiên phương án:

-   Đơn giản hơn.
-   Dễ hiểu hơn.
-   Ít phụ thuộc hơn.
-   Dễ kiểm thử hơn.
-   Dễ mở rộng hơn.

------------------------------------------------------------------------

# 17. Architecture Evolution

Kiến trúc được phát triển theo từng giai đoạn.

Foundation

↓

Stable Architecture

↓

Feature Expansion

↓

Optimization

↓

Production

Không đảo ngược thứ tự này.

------------------------------------------------------------------------

# 18. Final Principle

Một quyết định kỹ thuật được xem là tốt khi:

-   Không làm tăng phụ thuộc không cần thiết.
-   Không phá vỡ Design Contract.
-   Không làm mờ trách nhiệm của repository.
-   Không làm giảm khả năng mở rộng trong tương lai.
-   Giúp Platform trở nên ổn định hơn sau mỗi Sprint.
