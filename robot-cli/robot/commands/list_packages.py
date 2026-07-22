import click
from ..core import package

@click.command()
def list_packages():
    """List available and installed packages."""
    available = package.get_available_packages()
    installed = package.get_installed_packages()

    click.echo("📦 Available packages:")
    for p in available:
        status = "✅ installed" if p.name in installed else "⬜ not installed"
        click.echo(f"  - {p.name} v{p.version} ({p.type}) {status}")

    click.echo("")
    click.echo("Installed packages:")
    if installed:
        for name in installed:
            click.echo(f"  - {name}")
    else:
        click.echo("  (none)")