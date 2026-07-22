import click
import sys
from pathlib import Path
from ..core import config, utils

@click.command()
@click.option('--save', is_flag=True, help='Save results to history')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def benchmark(save, verbose):
    """Run benchmarks"""
    click.echo(" Running benchmarks...")
    runner = config.ROOT / "benchmarks" / "runner.py"
    if not runner.exists():
        click.echo("[FAILED] benchmarks/runner.py not found.", err=True)
        sys.exit(1)

    args = []
    if save:
        args.append("--save")
    if verbose:
        args.append("--verbose")

    result = utils.run_script(runner, args, capture=not verbose)
    if verbose:
        click.echo(result.stdout)
    if result.returncode != 0:
        click.echo(result.stderr, err=True)
        sys.exit(result.returncode)
    click.echo("[OK] Benchmark complete.")