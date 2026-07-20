# ARCHITECTURE.md

# Robot Development Platform Architecture

## 1. Vision

Robot Development Platform là nền tảng Robotics độc lập với Frontend và
Hardware.

## 2. Architecture Principles

-   Single Source of Truth
-   Frontend Independent
-   Hardware Independent
-   Layered Architecture
-   Artifact Driven Development
-   Repository Separation

## 3. High Level Architecture

``` text
Student
  │
  ▼
Frontend
  │
  ▼
Standard Python
  │
  ▼
Python AST
  │
  ▼
Robot Compiler
  │
  ▼
Bytecode
  │
  ▼
Robot VM
  │
  ▼
RobotAPI
  │
  ▼
Hardware
```

## 4. Repository Responsibilities

### robot-language

-   Define Specification
-   Validate
-   Generate Artifacts

Never: - Compile - Execute - Access Hardware

### robot-frontend

-   Rewrite AST
-   Mapping

Never: - Compile - Execute

### robot-compiler

-   Compile AST
-   Generate Bytecode

Never: - Access Hardware - Parse Specification

### robot-platform

-   Execute Bytecode
-   RobotAPI

Never: - Compile - Parse AST

## 5. Artifact Flow

``` text
api.yaml
   ↓
RobotLanguage
   ↓
Validator
   ↓
Generator
   ↓
Artifacts
   ↓
Compiler / Frontend / Runtime
```

Current Artifacts

-   opcode.py
-   opcode.json
-   function_registry.py
-   sdk/

## 6. Dependency Rules

-   Dependency một chiều.
-   Không circular dependency.
-   Không duplicate specification.
-   Mọi project chỉ đọc Artifact.

## 7. Runtime Flow

``` text
Program
 ↓
Fetch
 ↓
Decode
 ↓
Dispatch
 ↓
RobotAPI
 ↓
Hardware
```

## 8. Architecture Constraints

-   Một Specification duy nhất.
-   Không sửa Generated File.
-   Compiler không biết Hardware.
-   VM không biết AST.
-   Frontend không biết Bytecode.
-   Chỉ robot-language được đọc api.yaml.

## 9. Future Architecture

Foundation ↓ Artifact System ↓ Platform Description ↓ Runtime ABI ↓
Compiler Sync ↓ VM Sync ↓ Regression
