import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from . import config

PACKAGES_DIR = config.ROOT / "packages"
INSTALLED_DIR = config.ROOT / ".robot" / "installed"


class Package:
    def __init__(self, path: Path):
        self.path = path
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        meta_file = self.path / "package.yaml"
        if not meta_file.exists():
            raise FileNotFoundError(f"package.yaml not found in {self.path}")
        with open(meta_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @property
    def name(self) -> str:
        return self.metadata.get('name', self.path.name)

    @property
    def version(self) -> str:
        return self.metadata.get('version', '0.0.0')

    @property
    def description(self) -> str:
        return self.metadata.get('description', '')

    @property
    def type(self) -> str:
        return self.metadata.get('type', 'unknown')

    @property
    def targets(self) -> List[str]:
        return self.metadata.get('targets', [])

    def install(self):
        """Copy files to respective repositories."""
        installed_dir = INSTALLED_DIR / self.name
        installed_dir.mkdir(parents=True, exist_ok=True)

        # Lưu metadata đã cài đặt
        with open(installed_dir / "package.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(self.metadata, f)

        # Copy platform files
        if "platform" in self.targets:
            src_platform = self.path / "platform"
            if src_platform.exists():
                dst_platform = config.REPO_PLATFORM / "main" / "src"
                self._copy_dir(src_platform, dst_platform)

        # Copy compiler files
        if "compiler" in self.targets:
            src_compiler = self.path / "compiler"
            if src_compiler.exists():
                dst_compiler = config.REPO_COMPILER / "compiler"
                self._copy_dir(src_compiler, dst_compiler)

        # Copy frontend files
        if "frontend" in self.targets:
            src_frontend = self.path / "frontend"
            if src_frontend.exists():
                dst_frontend = config.REPO_FRONTEND / "frontend"
                self._copy_dir(src_frontend, dst_frontend)

        # Copy docs
        src_docs = self.path / "docs"
        if src_docs.exists():
            dst_docs = config.REPO_DOCS / "packages" / self.name
            self._copy_dir(src_docs, dst_docs)

    def _copy_dir(self, src: Path, dst: Path):
        if not src.exists():
            return
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, dirs_exist_ok=True)

    def uninstall(self):
        """Remove installed files (reverse of install)."""
        # Xóa các file đã copy
        if "platform" in self.targets:
            dst_platform = config.REPO_PLATFORM / "main" / "src"
            self._remove_package_files(self.path / "platform", dst_platform)

        if "compiler" in self.targets:
            dst_compiler = config.REPO_COMPILER / "compiler"
            self._remove_package_files(self.path / "compiler", dst_compiler)

        if "frontend" in self.targets:
            dst_frontend = config.REPO_FRONTEND / "frontend"
            self._remove_package_files(self.path / "frontend", dst_frontend)

        # Xóa thư mục đã cài đặt
        installed_dir = INSTALLED_DIR / self.name
        if installed_dir.exists():
            shutil.rmtree(installed_dir)

    def _remove_package_files(self, src: Path, dst: Path):
        if not src.exists():
            return
        for item in src.rglob("*"):
            if item.is_file():
                rel = item.relative_to(src)
                target = dst / rel
                if target.exists():
                    target.unlink()
        # Xóa các thư mục rỗng
        for item in sorted(src.rglob("*"), reverse=True):
            if item.is_dir():
                rel = item.relative_to(src)
                target = dst / rel
                if target.exists() and not any(target.iterdir()):
                    target.rmdir()


def get_available_packages() -> List[Package]:
    """List all available packages in PACKAGES_DIR."""
    if not PACKAGES_DIR.exists():
        return []
    packages = []
    for item in PACKAGES_DIR.iterdir():
        if item.is_dir() and (item / "package.yaml").exists():
            try:
                packages.append(Package(item))
            except Exception:
                pass
    return packages


def get_installed_packages() -> List[str]:
    """List names of installed packages."""
    if not INSTALLED_DIR.exists():
        return []
    return [item.name for item in INSTALLED_DIR.iterdir() if item.is_dir()]


def is_installed(package_name: str) -> bool:
    return (INSTALLED_DIR / package_name).exists()