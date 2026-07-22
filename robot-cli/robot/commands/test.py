import click
import sys
from pathlib import Path
from ..core import config, utils

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--json', 'json_output', help='Output JSON report file')
def test(verbose, json_output):
    click.echo("🧪 Running regression tests...")
    test_runner = config.ROOT / "tests" / "runner.py"
    if not test_runner.exists():
        click.echo("❌ tests/runner.py not found. Please create the regression framework.", err=True)
        sys.exit(1)

    args = []
    if verbose:
        args.append("--verbose")
    if json_output:
        args.extend(["--json", json_output])

    result = utils.run_script(test_runner, args, capture=not verbose)
    if verbose:
        click.echo(result.stdout)

    if result.returncode != 0:
        click.echo(result.stderr, err=True)
        sys.exit(result.returncode)

    click.echo("✅ All tests passed.")