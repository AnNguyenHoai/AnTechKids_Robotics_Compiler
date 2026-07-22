Robot Development Platform
Development Roadmap
Version: Foundation v1 (Draft) – Updated after Sprint 3

Vision
Xây dựng một Robot Development Platform hoàn chỉnh, mở rộng được, độc
lập với Frontend và Hardware, có khả năng hỗ trợ nhiều loại Robot, nhiều
ngôn ngữ lập trình và nhiều môi trường phát triển.

Roadmap Overview
Foundation (✅ Phase 0)
↓
Language Platform (✅ Sprint 1)
↓
Compiler Platform (✅ Sprint 2, ✅ Sprint 3)
↓
Runtime Platform (🔄 Sprint 4, 5)
↓
Developer Experience (⏳ Sprint 6+)
↓
Production Platform (📅 Future)
↓
Robot Ecosystem (📅 Future)

Legend: ✅ Completed, 🔄 In Progress, ⏳ Planned, 📅 Future

Phase 0 – Foundation (Completed)
Goal
Hoàn thiện nền tảng kiến trúc và build system.

Objectives
Architecture Documentation

Build System

Design Contract

Engineering Philosophy

Development Guide

Repository Structure

Deliverables
☑ Foundation Documentation (7 files)
☑ Stable Repository Structure
☑ Build Pipeline (robot-language)
☑ Design Contract
Exit Criteria
☑ Architecture Freeze
☑ Repository Responsibility ổn định
☑ Build Pipeline ổn định
Phase 1 – Language Platform (Completed)
Goal
Hoàn thiện Robot Language và Build System.

Objectives
Language API (api.yaml)

Validation Framework

Generator Framework

Artifact System

SDK Generation

Deliverables
☑ Stable Robot Language Specification
☑ Validators (Duplicate, Semantic, Reference)
☑ Generators (opcode.py, opcode.h, opcode.json, function_registry.py, registry.json, SDK)
☑ Artifact Installation (compiler + platform)
Sprint 1 – Opcode Synchronization (Completed)
Mục tiêu: Đồng bộ opcode giữa compiler và VM thông qua artifact.

Công việc:

Thêm internal category cho opcode nội bộ (LoadConst, Compare, Jump...).

Sinh opcode.h cho C++ runtime.

Cập nhật install.py để copy artifact sang compiler và platform.

Sửa compiler và VM để dùng chung opcode enum.

Kết quả:

Bytecode từ compiler được VM hiểu đúng.

Tất cả test basic pass.

Phase 2 – Compiler Platform (In Progress)
Goal
Hoàn thiện Robot Compiler với các tính năng cốt lõi.

Objectives
AST Traversal

Bytecode Generation

Program Construction

Symbol Management

Error Handling

Deliverables
☑ AST traversal cơ bản (assign, function def, call, expr)
☑ Bytecode generation
☑ Symbol table (biến, tạm)
☑ Control flow: if, while, break, continue
☑ Comparisons and boolean logic
☑ Arithmetic expressions (Sprint 3)
□ User-defined functions with parameters (Sprint 4)
□ Scope management (Sprint 4)
Sprint 2 – Compiler Uses Artifacts (Completed)
Mục tiêu: Compiler chỉ dùng artifact, không còn opcode tự viết tay.

Công việc:

Xóa OpcodeTable và các file opcode cũ.

Import Opcode enum từ generated/opcode.py.

Cập nhật tất cả handlers, emitter, tests.

Đồng bộ import function_registry từ artifact.

Kết quả:

Compiler hoàn toàn phụ thuộc vào artifact.

Không còn vi phạm Single Source of Truth.

Tất cả test pass.

Sprint 3 – Arithmetic Expressions (Completed)
Mục tiêu: Hỗ trợ biểu thức số học trong đối số hàm.

Công việc:

Thêm opcode số học vào spec: Add, Sub, Mul, Div, Mod, Pow, Neg.

Compiler: compile_expression xử lý ast.BinOp và ast.UnaryOp.

VM: Implement các opcode số học.

Frontend RoboSim: Chuyển đổi SetMoveRunSecond → seconds * 1000.

Kết quả:

Hỗ trợ: forward(5 + 3), wait(seconds * 1000).

Biểu thức chỉ hỗ trợ trong đối số hàm, không trong phép gán.

Tất cả test pass.

Sprint 4 – User-Defined Functions and Scope (Upcoming)
Mục tiêu: Compiler hỗ trợ hàm do người dùng định nghĩa với tham số và giá trị trả về.

Công việc dự kiến:

Symbol table có scope stack.

Function definition: lưu tham số và body.

Function call: truyền tham số, tạo frame mới.

Return value: lưu kết quả vào biến tạm.

Các tính năng con:

Hàm không tham số.

Hàm có tham số.

Hàm có giá trị trả về.

Hàm lồng nhau (nested functions) – có thể bỏ qua ban đầu.

Scope variables (local vs global).

Exit Criteria:

Demo chạy được với hàm tự định nghĩa.

Test pass.

Thời gian dự kiến: 5-7 ngày.

Sprint 5 – Sensor Integration (Upcoming)
Mục tiêu: Robot có thể đọc cảm biến và phản hồi.

Công việc dự kiến:

Thêm API cảm biến vào spec (read_ultrasonic, read_light, ...).

Thêm opcode ReadSensor.

Compiler: xử lý hàm đọc cảm biến.

VM: gọi RobotAPI để đọc giá trị và lưu vào biến.

Demo: vòng lặp đọc cảm biến, điều khiển động cơ dựa trên giá trị.

Exit Criteria:

Chương trình while distance < 20: forward(80) hoạt động.

Test pass.

Thời gian dự kiến: 3-4 ngày.

Phase 3 – Runtime Platform (Completed)
Goal
Hoàn thiện Robot VM với hiệu suất và tính năng nâng cao.

Objectives
Virtual Machine
Dispatch System
Runtime Context
RobotAPI
Debugging Support (cơ bản)

Deliverables
☑ Runtime ABI (VM_ABI.md)
☑ Complete VM Dispatcher
☑ Runtime Error Handling
☑ End-to-End Pipeline
☑ Regression Suite

...

Foundation v3 (✅ Sprint 14.6)
- Runtime Error Handling
- Foundation Freeze
- Tag: Foundation v1

Phase 4 – Developer Experience (Planning)
Goal
Tăng năng suất phát triển với công cụ hỗ trợ.

Objectives
CLI Tool

Build Tool

Testing Framework

Debugger

Features (Future)
Incremental Build

Build Cache

Auto Documentation

Code completion
Phase 4 – Documentation Generator (✅ Completed)
- Auto-generate opcode, language, SDK, RobotAPI references
- Integrated with `robot docs` command
- All docs are generated artifacts
Phase 5 – Production Platform (Planning)
Goal
Đưa nền tảng vào sử dụng thực tế.

Objectives
Packaging

Versioning

Release Process

CI/CD

Deliverables (Future)
Stable Release v1.0

Production Build

Release Package

Package Manager

Phase 6 – Robot Ecosystem (Vision)
Goal
Mở rộng hệ sinh thái với nhiều frontend và hardware.

Supported Frontends (Future)
☑ RoboSim (basic)
□ Blockly
□ Scratch
□ Python (direct)
Supported Hardware (Future)
□ Arduino (Uno, Mega)
□ ESP32
□ Raspberry Pi
□ STM32
Future Features
Cloud Build

Online Simulator

Remote Deployment

Plugin System

Cross-Project Roadmap
Documentation
☑ ARCHITECTURE.md
☑ BUILD_SYSTEM.md
☑ DESIGN_CONTRACT.md
☑ DEVELOPMENT_GUIDE.md
☑ ENGINEERING_PHILOSOPHY.md
☑ ROADMAP.md
☑ PROJECT_STATUS.md
□ CHANGELOG.md (optional)
Build System (robot-language)
☑ Artifact System
☑ Opcode Header Generator (C++)
☑ SDK Generation
□ Platform Description
□ Runtime ABI Generation
□ Incremental Build
□ Build Manifest
Compiler (robot-compiler)
☑ Variables
☑ Comparisons & Boolean
☑ Control flow (if, while, break, continue)
☑ Arithmetic Expressions
□ Functions
□ Scope
□ Collections (list, dict)
□ Classes (basic)
□ Optimization (constant folding, dead code elimination)
Runtime (robot-platform)
☑ Basic VM Skeleton
☑ Instruction Dispatch
☑ Comparisons & Arithmetic
□ Sensor Support
□ Error Handling
□ Debugger
□ Profiler
□ Runtime ABI
Frontend (robot-frontend-robosim)
☑ SetMoveRun, SetMoveStop, SetWaitForTime
☑ SetMoveRunSecond (with arithmetic)
□ Additional RoboSim APIs (SetLed, SetBeep...)
□ Error reporting (invalid direction)
Tooling
□ CLI Tool
□ Regression Test Framework
□ Packaging Scripts
□ CI/CD (GitHub Actions)
Milestones Timeline
Foundation v1 (✅ Completed)
Documentation Complete

Stable Architecture

Stable Build

Foundation v2 (✅ Completed)
Artifact System

Opcode Synchronization (Sprint 1)

Compiler Uses Artifacts (Sprint 2)

Compiler v1 (✅ Sprint 3)
Arithmetic Expressions (Sprint 3)

Compiler v2 (📅 Sprint 4)
Functions and Scope (Sprint 4)

Compiler v3 (📅 Sprint 5)
Sensor Integration (Sprint 5)

Runtime v1 (📅 Sprint 5)
Sensor Support

Basic Error Handling

Developer Tools v1 (📅 Sprint 6)
CLI Tool

Regression Test Framework

Production v1 (📅 Future)
Packaging

CI/CD

Ecosystem v1 (📅 Future)
Multi Frontend

Multi Hardware

Success Criteria
Dự án được xem là thành công khi:

☑ Có thể bổ sung Frontend mới mà không thay đổi Compiler.
☑ Có thể bổ sung Hardware mới mà không thay đổi Compiler.
☑ Mọi Repository có trách nhiệm rõ ràng.
☑ Build Pipeline ổn định.
□ Runtime ổn định.
□ Documentation luôn đồng bộ với hệ thống.
□ Platform có thể phát triển lâu dài mà không cần tái cấu trúc kiến trúc nền.

