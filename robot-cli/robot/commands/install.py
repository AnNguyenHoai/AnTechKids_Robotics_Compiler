import click
import sys
from pathlib import Path
from ..core import config, package

@click.command()
@click.argument('package_name')
def install(package_name):
    """Install a package."""
    click.echo(f"📦 Installing package: {package_name}")

    # Kiểm tra package có tồn tại không
    available = package.get_available_packages()
    pkg = None
    for p in available:
        if p.name == package_name:
            pkg = p
            break

    if pkg is None:
        click.echo(f"❌ Package '{package_name}' not found.", err=True)
        click.echo("Available packages:")
        for p in available:
            click.echo(f"  - {p.name} ({p.version})")
        sys.exit(1)

    # Kiểm tra đã cài đặt chưa
    if package.is_installed(package_name):
        click.echo(f"⚠️ Package '{package_name}' is already installed. Use `robot uninstall {package_name}` first.")
        sys.exit(1)

    # Cài đặt
    pkg.install()
    click.echo(f"✅ Package '{package_name}' installed successfully.")