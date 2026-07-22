import click
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from ..core import config, version as ver

@click.command()
@click.argument('version', required=False)
@click.option('--major', is_flag=True, help='Bump major version (x.0.0)')
@click.option('--minor', is_flag=True, help='Bump minor version (0.x.0)')
@click.option('--patch', is_flag=True, help='Bump patch version (0.0.x)')
@click.option('--message', '-m', help='Release message for notes')
def release(version, major, minor, patch, message):
    """Create a new release."""
    # Xác định phiên bản mới
    current = ver.get_version()
    if version:
        new_version = version
    elif major:
        parts = current.split('.')
        new_version = f"{int(parts[0]) + 1}.0.0"
    elif minor:
        parts = current.split('.')
        new_version = f"{parts[0]}.{int(parts[1]) + 1}.0"
    elif patch:
        parts = current.split('.')
        new_version = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
    else:
        click.echo("⚠️ Please specify a version or bump option (--major, --minor, --patch).", err=True)
        sys.exit(1)

    click.echo(f"📦 Creating release {new_version} (current: {current})")

    # Tạo thư mục release
    release_dir = config.ROOT / "releases" / f"v{new_version}"
    if release_dir.exists():
        click.echo(f"❌ Release {new_version} already exists.", err=True)
        sys.exit(1)
    release_dir.mkdir(parents=True)

    # Tạo release notes
    notes_file = release_dir / "release-notes.md"
    with open(notes_file, "w", encoding="utf-8") as f:
        f.write(f"# Release {new_version}\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n\n")
        if message:
            f.write(f"## Summary\n\n{message}\n\n")
        else:
            f.write("## Summary\n\n*Provide a summary of changes.*\n\n")
        f.write("## Changes\n\n- TBD\n\n")
        f.write("## Known Issues\n\n- TBD\n\n")
        f.write("## Migration Guide\n\n- None\n\n")

    # Cập nhật VERSION
    ver.set_version(new_version)

    # Cập nhật CHANGELOG.md
    changelog = config.ROOT / "CHANGELOG.md"
    if changelog.exists():
        content = changelog.read_text(encoding="utf-8")
    else:
        content = "# Changelog\n\n"

    # Thêm entry mới vào đầu
    entry = f"\n## v{new_version} ({datetime.now().strftime('%Y-%m-%d')})\n\n### Added\n- TBD\n\n### Fixed\n- TBD\n\n### Changed\n- TBD\n\n"
    new_content = f"# Changelog\n\n{entry}" + content.lstrip("# Changelog\n\n")
    changelog.write_text(new_content, encoding="utf-8")

    click.echo(f"✅ Release {new_version} created.")
    click.echo(f"   - Release notes: {notes_file}")
    click.echo(f"   - CHANGELOG updated")
    click.echo(f"   - Version updated to {new_version}")

    # (Optional) git commit and tag
    if click.confirm("Do you want to commit and tag this release with git?"):
        try:
            subprocess.run(["git", "add", "VERSION", "CHANGELOG.md", "releases/"], check=True)
            subprocess.run(["git", "commit", "-m", f"Release {new_version}"], check=True)
            subprocess.run(["git", "tag", f"v{new_version}"], check=True)
            click.echo(f"✅ Git commit and tag v{new_version} created.")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Git operation failed: {e}", err=True)
            sys.exit(1)