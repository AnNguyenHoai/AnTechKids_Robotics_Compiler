import os
from pathlib import Path

VERSION = "0.1.0"
LANG_SPEC_VERSION = "1.0.0"

# Đường dẫn gốc của workspace (giả sử robot-cli nằm cùng cấp với các repo khác)
ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Các thư mục repository
REPO_COMPILER = ROOT / "robot-compiler"
REPO_LANGUAGE = ROOT / "robot-language"
REPO_PLATFORM = ROOT / "robot-platform"
REPO_FRONTEND = ROOT / "robot-frontend-robosim"
REPO_DOCS = ROOT / "robot-docs"

# File test tổng hợp
TEST_SCRIPT = ROOT / "run_all_tests.py"