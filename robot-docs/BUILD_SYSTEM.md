# BUILD_SYSTEM.md

# Robot Development Platform

## Build System

Version: Foundation v1 (Draft)

------------------------------------------------------------------------

# 1. Purpose

Build System chịu trách nhiệm chuyển Robot Language Specification thành
các Artifact phục vụ cho toàn bộ nền tảng.

Build System không compile chương trình Robot.

Build System không execute chương trình Robot.

Build System chỉ sinh và phân phối Artifact.

------------------------------------------------------------------------

# 2. Build Architecture

``` text
api.yaml
    │
    ▼
RobotLanguage
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
Install
    │
    ▼
Consumer Repository
```

------------------------------------------------------------------------

# 3. Build Components

## Specification

Input duy nhất của Build System.

    api.yaml

Specification định nghĩa:

-   Category
-   Function
-   Opcode
-   Argument
-   Module
-   Handler

------------------------------------------------------------------------

## RobotLanguage

RobotLanguage là lớp truy cập duy nhất tới Specification.

Responsibilities

-   Load Specification
-   Query Specification
-   Cung cấp API cho Validator
-   Cung cấp API cho Generator

Forbidden

-   Generate File
-   Install Artifact
-   Compile Program

------------------------------------------------------------------------

## Validation

Validation chạy trước Generation.

Validator bao gồm:

-   Duplicate Validator
-   Semantic Validator
-   Reference Validator

Build sẽ dừng nếu Validation thất bại.

------------------------------------------------------------------------

## Generation

Generator chuyển Specification thành Artifact.

Generator chỉ đọc RobotLanguage.

Generator không đọc trực tiếp api.yaml.

Generator không ghi ra Repository khác.

------------------------------------------------------------------------

## Artifact

Artifact là đầu ra chuẩn của Build.

Current

-   opcode.py
-   opcode.json
-   function_registry.py
-   sdk/

Future

-   runtime_abi.json
-   dispatch_table
-   mapping_metadata
-   documentation

------------------------------------------------------------------------

## Install

Install chịu trách nhiệm phân phối Artifact.

Install không sinh Artifact.

Install không chỉnh sửa Artifact.

Install chỉ copy đúng phiên bản mới nhất.

------------------------------------------------------------------------

# 4. Build Pipeline

``` text
Specification

↓

Load

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
```

------------------------------------------------------------------------

# 5. Build Order

1.  Load Specification
2.  Validation
3.  Create Build Context
4.  Run Generators
5.  Produce Artifacts
6.  Install Artifacts
7.  Finish Build

------------------------------------------------------------------------

# 6. Build Context

BuildContext quản lý toàn bộ trạng thái Build.

Responsibilities

-   Output Path
-   Generated Path
-   Temporary State
-   Build Configuration

Không chứa Business Logic.

------------------------------------------------------------------------

# 7. Generator Rules

Generator

Có quyền

-   Đọc RobotLanguage
-   Sinh Artifact

Không được

-   Đọc api.yaml
-   Copy File
-   Sửa Repository khác
-   Thay đổi Build Context

------------------------------------------------------------------------

# 8. Artifact Rules

-   Một Artifact chỉ có một Producer.
-   Artifact là Read Only đối với Consumer.
-   Không sửa Generated Artifact bằng tay.
-   Artifact luôn được sinh từ Specification.

------------------------------------------------------------------------

# 9. Install Rules

Install chỉ có nhiệm vụ:

-   Copy
-   Replace
-   Synchronize

Không

-   Validate
-   Generate
-   Compile

------------------------------------------------------------------------

# 10. Consumer Rules

Các Consumer

-   robot-compiler
-   robot-frontend
-   robot-platform (future)

Chỉ được đọc Artifact.

Không được chỉnh sửa Artifact.

------------------------------------------------------------------------

# 11. Failure Policy

Build phải dừng khi:

-   Specification không hợp lệ.
-   Validation thất bại.
-   Generator thất bại.
-   Artifact không sinh thành công.
-   Install thất bại.

Không được bỏ qua lỗi.

------------------------------------------------------------------------

# 12. Future Build System

Future Build Pipeline

``` text
api.yaml

↓

RobotLanguage

↓

Validation

↓

Platform Description

↓

Generator

↓

Artifact

↓

Package

↓

Install

↓

Consumer
```

Future Features

-   Incremental Build
-   Parallel Generator
-   Artifact Cache
-   Build Manifest
-   Versioned Artifact
-   Runtime ABI Generation

------------------------------------------------------------------------

# 13. Design Rules

-   Build chỉ có một Entry Point.
-   BuildContext là nơi duy nhất quản lý Build State.
-   RobotLanguage là nơi duy nhất truy cập Specification.
-   Generator không biết Repository.
-   Install không biết Generator.
-   Consumer không biết Specification.
-   Artifact là hợp đồng giữa các Repository.

------------------------------------------------------------------------

# 14. Definition of Done

Build System được xem là hoàn chỉnh khi:

-   Build chạy từ một Entry Point.
-   Validation luôn chạy trước Generation.
-   Artifact được sinh đầy đủ.
-   Install đồng bộ tất cả Consumer.
-   Không còn Repository nào đọc trực tiếp Specification ngoài
    robot-language.
