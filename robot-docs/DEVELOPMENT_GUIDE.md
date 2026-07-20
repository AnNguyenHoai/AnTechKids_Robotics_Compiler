# DEVELOPMENT_GUIDE.md

# Robot Development Platform

## Development Guide

Version: Foundation v1 (Draft)

------------------------------------------------------------------------

# 1. Purpose

Tài liệu này định nghĩa quy trình phát triển chuẩn của Robot Development
Platform.

Mọi tính năng mới đều phải tuân theo quy trình này.

------------------------------------------------------------------------

# 2. Development Workflow

``` text
Requirement
    │
    ▼
Specification
    │
    ▼
Validation
    │
    ▼
Generation
    │
    ▼
Artifact
    │
    ▼
Compiler
    │
    ▼
Runtime
    │
    ▼
Regression
```

Không được bỏ qua bất kỳ bước nào.

------------------------------------------------------------------------

# 3. Feature Development Flow

1.  Phân tích yêu cầu.
2.  Xác định ảnh hưởng tới Specification.
3.  Cập nhật Specification.
4.  Build Artifact.
5.  Cập nhật Consumer.
6.  Regression Test.
7.  Cập nhật Documentation.

------------------------------------------------------------------------

# 4. Adding a New Robot API

``` text
Requirement
    ↓
api.yaml
    ↓
Validation
    ↓
Generator
    ↓
Artifact
    ↓
Compiler
    ↓
Runtime
    ↓
Test
```

Checklist

-   [ ] Specification
-   [ ] Validation
-   [ ] Artifact
-   [ ] Compiler
-   [ ] Runtime
-   [ ] Documentation
-   [ ] Regression

------------------------------------------------------------------------

# 5. Adding a New Generator

-   Tạo Generator mới.
-   Đăng ký trong Build System.
-   Sinh Artifact.
-   Kiểm tra Output.
-   Cập nhật Install.

Không sửa Generator hiện có nếu không cần thiết.

------------------------------------------------------------------------

# 6. Adding a New Artifact

Quy trình

1.  Thiết kế Artifact.
2.  Xây dựng Generator.
3.  Sinh Artifact.
4.  Install.
5.  Consumer sử dụng Artifact.

Rule

-   Một Artifact chỉ có một Producer.

------------------------------------------------------------------------

# 7. Modifying Compiler

Được phép

-   AST
-   Opcode Handling
-   Bytecode
-   Optimization

Không được

-   Parse Specification
-   Gọi RobotAPI
-   Chỉnh Frontend

------------------------------------------------------------------------

# 8. Modifying Runtime

Được phép

-   VM
-   Dispatch
-   RobotAPI

Không được

-   Compile
-   Parse AST
-   Parse Specification

------------------------------------------------------------------------

# 9. Modifying Frontend

Được phép

-   Rewrite
-   Mapping

Không được

-   Generate Bytecode
-   Execute
-   Parse Specification

------------------------------------------------------------------------

# 10. Build Checklist

-   [ ] Build thành công
-   [ ] Artifact được sinh
-   [ ] Install hoàn tất
-   [ ] Consumer đồng bộ

------------------------------------------------------------------------

# 11. Regression Checklist

-   [ ] Build
-   [ ] Compiler
-   [ ] VM
-   [ ] Existing Demo
-   [ ] Existing Artifact
-   [ ] Documentation

Không merge nếu Regression chưa hoàn thành.

------------------------------------------------------------------------

# 12. Commit Guideline

Một Commit chỉ nên:

-   Một Feature
-   Một Bug Fix
-   Một Refactor
-   Một Documentation Update

Không trộn nhiều mục đích trong cùng một Commit.

------------------------------------------------------------------------

# 13. Pull Request Checklist

-   [ ] Build thành công
-   [ ] Regression thành công
-   [ ] Documentation cập nhật
-   [ ] Không phá Design Contract
-   [ ] Không tạo Circular Dependency

------------------------------------------------------------------------

# 14. Code Review Checklist

-   Đúng Responsibility.
-   Đúng Layer.
-   Không duplicate logic.
-   Không sửa Generated File.
-   Không thêm dependency không cần thiết.

------------------------------------------------------------------------

# 15. Documentation Checklist

Sau mỗi Feature cần cập nhật nếu cần:

-   PROJECT_STATUS.md
-   ARCHITECTURE.md
-   BUILD_SYSTEM.md
-   DESIGN_CONTRACT.md
-   DEVELOPMENT_GUIDE.md
-   ENGINEERING_PHILOSOPHY.md
-   ROADMAP.md

------------------------------------------------------------------------

# 16. Definition of Done

Một Feature được xem là hoàn thành khi:

-   Requirement hoàn thành.
-   Code hoàn thành.
-   Build thành công.
-   Regression thành công.
-   Documentation cập nhật.
-   Pull Request được review.
-   Không vi phạm Design Contract.
