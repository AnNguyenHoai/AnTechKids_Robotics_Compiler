# PROJECT_STATUS.md

# Robot Development Platform

**Version:** Foundation v0.2

**Last Update:** Foundation Architecture Review

------------------------------------------------------------------------

# 1. Project Vision

Robot Development Platform là một nền tảng hoàn chỉnh dành cho Robotics
Education.

Mục tiêu của hệ thống là cho phép học sinh lập trình Robot bằng nhiều
Frontend khác nhau (RoboSim, Blockly, Scratch, Python...), sau đó biên
dịch thành Robot Bytecode và thực thi trên nhiều nền tảng phần cứng khác
nhau.

Toàn bộ hệ thống được thiết kế theo hướng:

-   Hardware Independent
-   Frontend Independent
-   Modular
-   Extensible

Robot Hardware chỉ là tầng cuối cùng của hệ thống.

------------------------------------------------------------------------

# 2. High Level Architecture

``` text
                  Student
                     │
                     ▼
          RoboSim / Blockly / IDE
                     │
                     ▼
              Robot Frontend
                     │
              Standard Python
                     │
                     ▼
             Python Standard AST
                     │
                     ▼
             Robot Compiler
                     │
              Bytecode Program
                     │
                     ▼
          Robot Virtual Machine
                     │
                     ▼
                Robot API
                     │
                     ▼
              Robot Hardware
```

------------------------------------------------------------------------

# 3. Repository Overview

## robot-language

Single Source of Truth.

-   Định nghĩa Robot Language Specification.
-   Không compile.
-   Không execute.
-   Không biết AST.
-   Sinh toàn bộ Artifact cho các repository khác.

## robot-frontend-robosim

Frontend Adapter.

-   Rewrite RoboSim API sang Robot Language API.
-   Không compile.
-   Không biết VM.
-   Không biết Hardware.

## robot-compiler

Compiler.

-   Compile Standard Python AST.
-   Sinh Robot Bytecode.
-   Không biết RoboSim.
-   Không execute.

## robot-platform

Runtime.

-   Execute Robot Bytecode.
-   Không parse Python.
-   Không compile.
-   Giao tiếp phần cứng thông qua RobotAPI.

------------------------------------------------------------------------

# 4. Repository Structure

## robot-language

### specification/

-   **api.yaml** --- Single Source of Truth.

### language/

-   **model.py** --- RobotLanguage Service, load specification và cung
    cấp Query API.

### validation/

-   **base_validator.py** --- Abstract validator.
-   **duplicate_validator.py** --- Duplicate validation.
-   **semantic_validator.py** --- Semantic validation.
-   **reference_validator.py** --- Reference validation.

### generators/

-   **base_generator.py** --- Abstract generator.
-   **registry_generator.py** --- Sinh function registry.
-   **opcode_generator.py** --- Sinh opcode.py.
-   **opcode_json_generator.py** --- Sinh opcode.json.
-   **sdk_generator.py** --- Sinh Python SDK.

### build/

-   **build.py** --- Build entry.
-   **builder.py** --- Điều phối Build Pipeline.
-   **context.py** --- BuildContext.
-   **artifacts.py** --- Đăng ký Artifact.
-   **install.py** --- Cài đặt Artifact sang project khác.

### generated/

-   Artifact sinh tự động. Không sửa bằng tay.

### sdk/

-   Python SDK.

------------------------------------------------------------------------

## robot-compiler

### compiler/

-   **compiler.py** --- Compiler chính.
-   **instruction.py** --- Instruction model.
-   **program.py** --- Bytecode Program.
-   **opcode.py** --- Opcode definition.
-   **emitter.py** --- Sinh generatedProgram.h.
-   **symbol_table.py** --- Symbol management.
-   **patch.py** --- Jump backpatch.
-   **label.py** --- Label management.

### handlers/

-   **motion_handler.py** --- Motion instruction.
-   **compare_handler.py** --- Compare instruction.
-   **bool_handler.py** --- Boolean instruction.
-   **system_handler.py** --- Wait/System instruction.

### generated/

-   Artifact từ robot-language.

------------------------------------------------------------------------

## robot-frontend-robosim

### frontend/

-   **compiler.py** --- Frontend entry.
-   **transformer.py** --- AST rewrite.
-   **mapping.py** --- RoboSim ↔ Robot Language mapping.

### examples/

-   Ví dụ.

### test/

-   Regression test.

------------------------------------------------------------------------

## robot-platform

### VM/

-   **VM.cpp** --- Main execution loop.
-   **Instruction.h** --- Instruction format.
-   **Opcode.h** --- Opcode definition.
-   **Program.h** --- Program model.
-   **VMContext.h** --- Runtime context.

### Robot/

-   **RobotAPI.h** --- Hardware abstraction.
-   **RobotAPI.cpp** --- Hardware implementation.

------------------------------------------------------------------------

# 5. Current End-to-End Flow

``` text
RoboSim Program
        │
        ▼
Frontend Rewrite
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
Bytecode Program
        │
        ▼
generatedProgram.h
        │
        ▼
Robot VM
        │
        ▼
RobotAPI
        │
        ▼
Robot Hardware
```

------------------------------------------------------------------------

# 6. Artifact Flow

``` text
api.yaml
   │
   ▼
RobotLanguage
   │
   ▼
Validator
   │
   ▼
Generator
   │
   ▼
Artifacts
   │
   ├── function_registry.py
   ├── opcode.py
   ├── opcode.json
   └── sdk/
```

  Artifact               Producer         Consumer
  ---------------------- ---------------- ----------------
  function_registry.py   robot-language   robot-compiler
  opcode.py              robot-language   robot-compiler
  opcode.json            robot-language   robot-compiler
  sdk/\*                 robot-language   robot-frontend

------------------------------------------------------------------------

# 7. Dependency Graph

``` text
robot-language
        │
        ▼
Generated Artifact
        │
        ▼
robot-compiler
        │
        ▼
Program
        │
        ▼
robot-platform
        │
        ▼
RobotAPI
        │
        ▼
Robot Hardware
```

------------------------------------------------------------------------

# 8. Current Progress

## robot-language

-   ★★★★★ Specification
-   ★★★★★ Validator
-   ★★★★★ Generator
-   ★★★★☆ Build Pipeline
-   ★★★☆☆ Artifact Management

## robot-compiler

-   ★★★★★ AST Traversal
-   ★★★★★ Variable
-   ★★★★★ If / While
-   ★★★★☆ Motion
-   ★★★☆☆ Boolean
-   ★★☆☆☆ Compare
-   ☆☆☆☆☆ Function
-   ☆☆☆☆☆ Expression

## robot-platform

-   ★★★★☆ VM Core
-   ★★★★☆ Instruction
-   ★★★★☆ Program
-   ★★★☆☆ Compare
-   ★★☆☆☆ Boolean
-   ☆☆☆☆☆ Call Stack
-   ☆☆☆☆☆ Memory Model

## robot-frontend

-   ★★★★☆ RoboSim Adapter
-   ★★★★☆ AST Rewrite
-   ★★★☆☆ Mapping
-   ☆☆☆☆☆ Blockly
-   ☆☆☆☆☆ Scratch

------------------------------------------------------------------------

# 9. Design Principles

1.  Specification chỉ tồn tại tại api.yaml.
2.  RobotLanguage là Single Source of Truth.
3.  Compiler chỉ Compile.
4.  Frontend chỉ Rewrite.
5.  VM chỉ Execute.
6.  Hardware chỉ nằm trong RobotAPI.
7.  Không sửa Generated File.
8.  Một Commit = Một Feature.
9.  Regression sau mỗi Commit.
10. BuildContext quản lý Build Environment.
11. Generator không quản lý Path.
12. Các project chỉ sử dụng Artifact.

------------------------------------------------------------------------

# 10. AI Working Rules

1.  Không suy đoán source code.
2.  Nếu thiếu context phải yêu cầu cung cấp file.
3.  Không refactor khi chưa xem source.
4.  Luôn ghi rõ Modified / Added / Deleted.
5.  Một Commit = Một Feature.
6.  Ưu tiên thay đổi nhỏ.
7.  Regression sau thay đổi.
8.  Không hardcode Opcode.
9.  Không đọc api.yaml ngoài RobotLanguage.
10. Không bypass Artifact.
11. Không sửa Generated File.
12. Không duplicate Specification.

------------------------------------------------------------------------

# 11. Foundation Roadmap

-   Phase 1 --- Language Specification ✅
-   Phase 2 --- Validator Pipeline ✅
-   Phase 3 --- Generator Pipeline ✅
-   Phase 4 --- Artifact Expansion 🔄
-   Phase 5 --- Compiler Synchronization
-   Phase 6 --- VM Synchronization
-   Phase 7 --- Regression
-   Phase 8 --- Distribution

------------------------------------------------------------------------

# 12. AI Context

PROJECT_STATUS.md là tài liệu trung tâm của Robot Development Platform.

Mọi AI Assistant phải đọc tài liệu này trước khi sửa code.

Nếu có mâu thuẫn giữa suy luận và tài liệu này thì ưu tiên
PROJECT_STATUS.md.

Sau mỗi Sprint cần cập nhật lại tài liệu.
