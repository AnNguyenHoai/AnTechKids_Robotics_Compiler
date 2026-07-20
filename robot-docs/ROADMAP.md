# ROADMAP.md

# Robot Development Platform

## Development Roadmap

Version: Foundation v1 (Draft)

------------------------------------------------------------------------

# Vision

Xây dựng một Robot Development Platform hoàn chỉnh, mở rộng được, độc
lập với Frontend và Hardware, có khả năng hỗ trợ nhiều loại Robot, nhiều
ngôn ngữ lập trình và nhiều môi trường phát triển.

------------------------------------------------------------------------

# Roadmap Overview

    Foundation

    ↓

    Language Platform

    ↓

    Compiler Platform

    ↓

    Runtime Platform

    ↓

    Developer Experience

    ↓

    Production Platform

    ↓

    Robot Ecosystem

------------------------------------------------------------------------

# Phase 0 - Foundation

## Goal

Hoàn thiện nền tảng kiến trúc.

### Objectives

-   Architecture
-   Build System
-   Design Contract
-   Engineering Philosophy
-   Development Guide
-   Documentation

### Deliverables

-   Foundation Documentation
-   Stable Repository Structure
-   Stable Build Pipeline
-   Stable Design Contract

### Exit Criteria

-   Architecture Freeze
-   Repository Responsibility ổn định
-   Build Pipeline ổn định

------------------------------------------------------------------------

# Phase 1 - Language Platform

## Goal

Hoàn thiện Robot Language.

### Objectives

-   Language API
-   Validation
-   Generator Framework
-   Artifact Framework
-   SDK Generation

### Deliverables

-   Stable Robot Language
-   Artifact System
-   Generator Framework

### Future Features

-   Platform Description
-   Metadata Generation
-   Runtime ABI Generation

------------------------------------------------------------------------

# Phase 2 - Compiler Platform

## Goal

Hoàn thiện Robot Compiler.

### Objectives

-   AST Traversal
-   Opcode Generation
-   Program Generation
-   Error Handling
-   Symbol Management

### Deliverables

-   Stable Compiler
-   Complete Bytecode Generation

### Future Features

-   Optimization
-   Constant Folding
-   Dead Code Elimination
-   Peephole Optimization

------------------------------------------------------------------------

# Phase 3 - Runtime Platform

## Goal

Hoàn thiện Robot Runtime.

### Objectives

-   Virtual Machine
-   Dispatch System
-   Runtime Context
-   RobotAPI

### Deliverables

-   Stable Runtime
-   Stable Instruction Set

### Future Features

-   Runtime ABI
-   Debug Runtime
-   Performance Profiling

------------------------------------------------------------------------

# Phase 4 - Developer Experience

## Goal

Tăng năng suất phát triển.

### Objectives

-   CLI
-   Build Tool
-   Testing Tool
-   Debug Tool

### Deliverables

-   Developer Toolkit
-   Regression Framework

### Future Features

-   Incremental Build
-   Build Cache
-   Auto Documentation

------------------------------------------------------------------------

# Phase 5 - Production Platform

## Goal

Đưa nền tảng vào sử dụng thực tế.

### Objectives

-   Packaging
-   Versioning
-   Release Process
-   CI/CD

### Deliverables

-   Stable Release
-   Production Build
-   Release Package

### Future Features

-   Package Manager
-   Plugin System

------------------------------------------------------------------------

# Phase 6 - Robot Ecosystem

## Goal

Mở rộng hệ sinh thái.

### Objectives

-   Multiple Frontends
-   Multiple Robot Platforms
-   Multiple Hardware Drivers

### Deliverables

Supported Frontends

-   RoboSim
-   Blockly
-   Scratch
-   Python

Supported Hardware

-   Arduino
-   ESP32
-   Raspberry Pi
-   STM32

### Future Features

-   Cloud Build
-   Online Simulator
-   Remote Deployment

------------------------------------------------------------------------

# Cross-Project Roadmap

## Documentation

-   PROJECT_STATUS.md
-   ARCHITECTURE.md
-   BUILD_SYSTEM.md
-   DESIGN_CONTRACT.md
-   ENGINEERING_PHILOSOPHY.md
-   DEVELOPMENT_GUIDE.md
-   ROADMAP.md

------------------------------------------------------------------------

## Build System

-   Artifact System
-   Platform Description
-   Runtime ABI
-   Incremental Build
-   Build Manifest

------------------------------------------------------------------------

## Compiler

-   Expressions
-   Variables
-   Functions
-   Collections
-   Classes
-   Optimization

------------------------------------------------------------------------

## Runtime

-   Instruction Set
-   VM Optimization
-   Debugger
-   Runtime Profiler

------------------------------------------------------------------------

## Frontend

-   RoboSim
-   Blockly
-   Scratch
-   Python

------------------------------------------------------------------------

## Tooling

-   CLI
-   Testing
-   Regression
-   Packaging

------------------------------------------------------------------------

# Milestones

## Foundation v1

-   Documentation Complete
-   Stable Architecture
-   Stable Build

## Foundation v2

-   Artifact Platform
-   Platform Description
-   Runtime ABI

## Platform v1

-   Stable Language
-   Stable Compiler
-   Stable Runtime

## Platform v2

-   Production Ready

## Platform v3

-   Multi Frontend
-   Multi Hardware

------------------------------------------------------------------------

# Success Criteria

Dự án được xem là thành công khi:

-   Có thể bổ sung Frontend mới mà không thay đổi Compiler.
-   Có thể bổ sung Hardware mới mà không thay đổi Compiler.
-   Mọi Repository có trách nhiệm rõ ràng.
-   Build Pipeline ổn định.
-   Runtime ổn định.
-   Documentation luôn đồng bộ với hệ thống.
-   Platform có thể phát triển lâu dài mà không cần tái cấu trúc kiến
    trúc nền.
