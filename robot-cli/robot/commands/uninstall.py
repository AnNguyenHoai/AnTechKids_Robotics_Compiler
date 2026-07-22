import click
import sys
from ..core import package

@click.command()
@click.argument('package_name')
def uninstall(package_name):
    """Uninstall a package."""
    click.echo(f"🗑️ Uninstalling package: {package_name}")

    if not package.is_installed(package_name):
        click.echo(f"❌ Package '{package_name}' is not installed.", err=True)
        sys.exit(1)

    # Tìm package đã cài đặt
    available = package.get_available_packages()
    pkg = None
    for p in available:
        if p.name == package_name:
            pkg = p
            break

    if pkg is None:
        # Package không còn trong danh sách, nhưng đã cài đặt
        # Xóa thủ công
        from . import config
        import shutil
        installed_dir = config.ROOT / ".robot" / "installed" / package_name
        if installed_dir.exists():
            shutil.rmtree(installed_dir)
        click.echo(f"✅ Package '{package_name}' uninstalled (metadata removed).")
        return

    pkg.uninstall()
    click.echo(f"✅ Package '{package_name}' uninstalled successfully.")