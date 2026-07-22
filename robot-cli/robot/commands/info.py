import click
from ..core import config

@click.command()
def info():
    """Display detailed information about the platform."""
    click.echo("📋 Robot Development Platform Information")
    click.echo(f"  Platform: Robot Development Platform")
    click.echo(f"  CLI Version: {config.VERSION}")
    click.echo(f"  Language Spec: {config.LANG_SPEC_VERSION}")
    click.echo(f"  Repository Root: {config.ROOT}")
    click.echo("")
    click.echo("  Repositories:")
    click.echo(f"    - Compiler: {config.REPO_COMPILER}")
    click.echo(f"    - Language: {config.REPO_LANGUAGE}")
    click.echo(f"    - Platform: {config.REPO_PLATFORM}")
    click.echo(f"    - Frontend: {config.REPO_FRONTEND}")
    click.echo(f"    - Docs: {config.REPO_DOCS}")