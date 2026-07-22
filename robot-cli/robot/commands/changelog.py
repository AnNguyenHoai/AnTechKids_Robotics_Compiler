import click
from pathlib import Path
from ..core import config

@click.command()
@click.option('--view', '-v', is_flag=True, help='View full changelog')
def changelog(view):
    """Display the changelog."""
    changelog_file = config.ROOT / "CHANGELOG.md"
    if not changelog_file.exists():
        click.echo("❌ CHANGELOG.md not found.", err=True)
        return

    if view:
        content = changelog_file.read_text(encoding="utf-8")
        click.echo(content)
    else:
        # Hiển thị tóm tắt các phiên bản
        lines = changelog_file.read_text(encoding="utf-8").splitlines()
        versions = []
        for line in lines:
            if line.startswith("## v"):
                # Lấy version và date
                versions.append(line.strip())
        if versions:
            click.echo("📋 Available releases:")
            for v in versions:
                click.echo(f"  {v}")
        else:
            click.echo("No releases found.")