# Toolchain Overview

This document describes the developer tools provided for building and deploying robot programs.

## Tools Directory

All tools are located in the `tools/` directory at the repository root.

### `rewrite.py`

Converts RoboSim source to Standard Robot API.

**Usage:**
```bash
python tools/rewrite.py --input <source.py> --output <output.rewrite.py>
Output: Only the .rewrite.py file. No compilation occurs.

compile.py
Compiles Standard Robot API source (.rewrite.py) to a C++ header.

Usage:

bash
python tools/compile.py --input <source.rewrite.py> [--output <program.h>] [--report <report.json>]
If --output is omitted, the output is placed in build/<basename>/program.h and build/<basename>/compile_report.json.

Note: The input file must have the extension .rewrite.py. The compiler will reject other files.

build.py
Full build pipeline: rewrite + compile.

Usage:

bash
python tools/build.py --input <source.py> [--build-dir <dir>] [--output <program.h>]
If --build-dir is omitted, the output is placed in build/<basename>/.

flash.py
Copies the generated header to the firmware project and uploads to ESP32.

Usage:

bash
python tools/flash.py --build-dir <build_dir>
Requires PlatformIO installed and the ESP32 connected.

golden_build.py
Validates all golden programs by building each one and collecting statistics.

Usage:

bash
python tools/golden_build.py
Produces build/golden_summary.json.

Integration with Robot CLI
The robot CLI tool integrates these tools via the build command:

bash
robot build --file program.py --build-dir build/my_program
Architecture Reminder
Frontend (rewrite.py) only generates .rewrite.py. It does not import or call the compiler.

Compiler (compile.py) only accepts .rewrite.py files. It does not know about RoboSim source.

The two stages are completely independent and communicate only through the .rewrite.py artifact.

Future Extensions
tools/debug.py: source-level debugging

tools/simulate.py: program simulation

tools/package.py: create deployable packages

text

---

## 9. Xóa dòng import `RoboSimCompiler` trong các file khác (kiểm tra toàn bộ codebase)

Không có file nào khác import `RoboSimCompiler` ngoài các file đã sửa. Đảm bảo không còn.

---

## 10. Chạy thử nghiệm

Sau khi thực hiện các thay đổi trên, chạy toàn bộ test để đảm bảo không regression:

```bash
python run_all_tests.py