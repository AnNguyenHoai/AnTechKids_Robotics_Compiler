# DESIGN_CONTRACT.md

# Robot Development Platform

## Design Contract

Version: Foundation v1 (Draft)

------------------------------------------------------------------------

# 1. Purpose

Design Contract định nghĩa ranh giới trách nhiệm giữa các repository.

Mọi repository phải tuân thủ tài liệu này.

Nếu có mâu thuẫn giữa implementation và Design Contract thì Design
Contract được ưu tiên xem xét trước khi thay đổi kiến trúc.

------------------------------------------------------------------------

# 2. Core Principles

-   Single Source of Truth
-   Single Responsibility
-   Layered Architecture
-   Artifact Driven Development
-   Dependency Direction
-   Hardware Independence
-   Frontend Independence
-   Generated Code First

------------------------------------------------------------------------

# 3. Repository Contracts

## robot-language

### Owns

-   Language Specification
-   Validator
-   Generator
-   Artifact Definition
-   SDK Generation

### Provides

-   Language API
-   Generated Artifacts

### Must Never

-   Compile Robot Program
-   Execute Robot Program
-   Access Robot Hardware
-   Parse AST

------------------------------------------------------------------------

## robot-frontend

### Owns

-   Frontend Adapter
-   AST Rewrite
-   API Mapping

### Provides

-   Standard Python Source

### Must Never

-   Generate Bytecode
-   Execute Program
-   Access Hardware
-   Parse Specification

------------------------------------------------------------------------

## robot-compiler

### Owns

-   AST Traversal
-   Bytecode Generation
-   Program Construction
-   Symbol Management

### Provides

-   Robot Program
-   Bytecode

### Must Never

-   Read api.yaml
-   Access Hardware
-   Execute Program
-   Rewrite Frontend Source

------------------------------------------------------------------------

## robot-platform

### Owns

-   Runtime
-   Virtual Machine
-   RobotAPI
-   Instruction Dispatch

### Provides

-   Robot Execution

### Must Never

-   Compile
-   Parse AST
-   Parse Specification
-   Rewrite Source Code

------------------------------------------------------------------------

# 4. Layer Contracts

Application Layer

-   Business Logic

Frontend Layer

-   Rewrite Source

Language Layer

-   Specification
-   Validation
-   Artifact

Compiler Layer

-   AST
-   Bytecode

Runtime Layer

-   Execute

Hardware Layer

-   Device Driver

------------------------------------------------------------------------

# 5. Dependency Contract

Allowed

    robot-language
          │
          ▼
    Generated Artifact
          │
     ┌────┼────┐
     ▼    ▼    ▼
    Frontend Compiler Runtime

Forbidden

-   Circular Dependency
-   Reverse Dependency
-   Shared Mutable State
-   Repository-to-Repository Business Logic

------------------------------------------------------------------------

# 6. Artifact Contract

Rules

-   Một Artifact chỉ có một Producer.
-   Artifact chỉ được sinh từ Specification.
-   Consumer không được sửa Artifact.
-   Generated File không sửa bằng tay.

------------------------------------------------------------------------

# 7. Specification Contract

Rules

-   Chỉ robot-language được đọc api.yaml.
-   Không repository nào khác parse Specification.
-   Mọi dữ liệu đều phải đi qua RobotLanguage.

------------------------------------------------------------------------

# 8. Build Contract

Build Flow

Specification

↓

Validation

↓

Generation

↓

Artifact

↓

Install

↓

Consumer

Rules

-   Validation luôn chạy trước.
-   Generator không copy file.
-   Install không generate file.
-   Consumer không build Artifact.

------------------------------------------------------------------------

# 9. Runtime Contract

Compiler tạo Program.

VM thực thi Program.

RobotAPI giao tiếp Hardware.

Compiler không gọi RobotAPI.

VM không compile.

Hardware không biết Compiler.

------------------------------------------------------------------------

# 10. Development Contract

Khi thêm Feature mới

1.  Cập nhật Specification.
2.  Validation.
3.  Generation.
4.  Artifact.
5.  Compiler.
6.  Runtime.
7.  Regression.

Không được bỏ qua bước.

------------------------------------------------------------------------

# 11. Naming Contract

-   Một khái niệm chỉ có một tên.
-   Không viết tắt khi không cần thiết.
-   Tên Generator kết thúc bằng Generator.
-   Tên Validator kết thúc bằng Validator.
-   Generated Folder chỉ chứa Generated File.

------------------------------------------------------------------------

# 12. Architecture Freeze

Foundation được xem là ổn định khi:

-   Repository Responsibility không đổi.
-   Dependency không đổi.
-   Build Pipeline không đổi.
-   Runtime Pipeline không đổi.

Sau thời điểm này chỉ bổ sung Feature, không thay đổi kiến trúc nền nếu
không có quyết định thiết kế mới.

------------------------------------------------------------------------

# 13. Definition of Done

Design Contract hoàn thành khi:

-   Mọi repository có trách nhiệm rõ ràng.
-   Không còn dependency mơ hồ.
-   Không còn repository làm nhiều vai trò.
-   Mọi thành viên có thể xác định nơi cần thay đổi khi thêm một tính
    năng mới.
