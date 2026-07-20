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

------------------------------------------------------------------------

3. Feature Development Flow
Phân tích yêu cầu.

Xác định ảnh hưởng tới Specification.

Cập nhật Specification.

Build Artifact.

Cập nhật Consumer.

Regression Test.

Cập nhật Documentation.

4. Build and Install Artifacts
Sau khi thay đổi api.yaml (thêm hàm mới, sửa opcode, v.v.), cần chạy build để sinh artifact mới:

bash
cd robot-language
python build.py
Lệnh này sẽ:

Load specification

Chạy validators (Duplicate, Semantic, Reference)

Sinh các artifact (opcode.py, opcode.h, function_registry.py, sdk, ...)

Sau đó, chạy install để phân phối artifact đến các consumer:

bash
python install.py
Install sẽ copy các file sinh ra vào đúng thư mục của từng consumer:

robot-compiler/compiler/generated/ (các file .py)

robot-platform/main/include/generated/ (opcode.h)

Quy tắc: Tuyệt đối không sửa tay bất kỳ file nào trong thư mục generated/. Mọi thay đổi đều phải thông qua api.yaml và build.

5. Adding a New Robot API
text
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
Checklist

□ Specification
□ Validation
□ Artifact
□ Compiler
□ Runtime
□ Documentation
□ Regression
6. Adding a New Generator
Tạo Generator mới.

Đăng ký trong Build System.

Sinh Artifact.

Kiểm tra Output.

Cập nhật Install.

Không sửa Generator hiện có nếu không cần thiết.

7. Adding a New Artifact
Quy trình

Thiết kế Artifact.

Xây dựng Generator.

Sinh Artifact.

Install.

Consumer sử dụng Artifact.

Rule

Một Artifact chỉ có một Producer.

8. Modifying Compiler
Được phép

AST

Opcode Handling

Bytecode

Optimization

Không được

Parse Specification

Gọi RobotAPI

Chỉnh Frontend

9. Modifying Runtime
Được phép

VM

Dispatch

RobotAPI

Không được

Compile

Parse AST

Parse Specification

10. Modifying Frontend
Được phép

Rewrite

Mapping

Không được

Generate Bytecode

Execute

Parse Specification

11. Build Checklist
□ Build thành công
□ Artifact được sinh
□ Install hoàn tất
□ Consumer đồng bộ
12. Regression Checklist
□ Build
□ Compiler
□ VM
□ Existing Demo
□ Existing Artifact
□ Documentation
Không merge nếu Regression chưa hoàn thành.

13. Commit Guideline
Một Commit chỉ nên:

Một Feature

Một Bug Fix

Một Refactor

Một Documentation Update

Không trộn nhiều mục đích trong cùng một Commit.

14. Pull Request Checklist
□ Build thành công
□ Regression thành công
□ Documentation cập nhật
□ Không phá Design Contract
□ Không tạo Circular Dependency
15. Code Review Checklist
Đúng Responsibility.

Đúng Layer.

Không duplicate logic.

Không sửa Generated File.

Không thêm dependency không cần thiết.

16. Documentation Checklist
Sau mỗi Feature cần cập nhật nếu cần:

PROJECT_STATUS.md

ARCHITECTURE.md

BUILD_SYSTEM.md

DESIGN_CONTRACT.md

DEVELOPMENT_GUIDE.md

ENGINEERING_PHILOSOPHY.md

ROADMAP.md

17. Definition of Done
Một Feature được xem là hoàn thành khi:

Requirement hoàn thành.

Code hoàn thành.

Build thành công.

Regression thành công.

Documentation cập nhật.

Pull Request được review.

Không vi phạm Design Contract.