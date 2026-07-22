import click
from ..core import config

@click.command()
def version():
    """Show version of the Robot Development Platform."""
    click.echo(f"Robot Development Platform version {config.VERSION}")
    click.echo(f"Language Specification version {config.LANG_SPEC_VERSION}")