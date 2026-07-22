import subprocess
import sys
from pathlib import Path

def run_script(script_path, args=None, capture=True):
    """Chạy một script Python và trả về kết quả."""
    if args is None:
        args = []
    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd, capture_output=capture, text=True)
    return result

def check_repo_exists(repo_path):
    """Kiểm tra repository có tồn tại không."""
    return repo_path.exists() and repo_path.is_dir()