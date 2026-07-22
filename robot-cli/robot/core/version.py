from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parent.parent.parent.parent / "VERSION"

def get_version():
    """Đọc phiên bản từ file VERSION."""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "0.0.0"

def set_version(version):
    """Ghi phiên bản vào file VERSION."""
    VERSION_FILE.write_text(version.strip() + "\n")