import click
from ..core import plugin

@click.command()
@click.option('--type', '-t', help='Filter by plugin type')
def plugin_list(type):
    """List available plugins."""
    plugins = plugin.discover_plugins(type)
    click.echo(f"📦 Available plugins ({len(plugins)} found):")
    for p in plugins:
        click.echo(f"  - {p.name} ({p.type}) -> {p.entry}")