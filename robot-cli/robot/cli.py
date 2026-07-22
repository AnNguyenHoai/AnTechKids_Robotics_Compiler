import click
from .commands import build, test, doctor, version, info
from .commands import benchmark
from .commands import docs
from .commands import release, changelog
from .commands import install, list_packages, uninstall
from .commands import plugin as plugin_cmd


@click.group()
def cli():
    """Robot Development Platform CLI
    
    Unified command-line tool for the Robot Development Platform.
    """
    pass

cli.add_command(build.build)
cli.add_command(test.test)
cli.add_command(doctor.doctor)
cli.add_command(version.version)
cli.add_command(info.info)
cli.add_command(benchmark.benchmark)
cli.add_command(docs.docs)
cli.add_command(release.release)
cli.add_command(changelog.changelog)
cli.add_command(install.install)
cli.add_command(list_packages.list_packages)
cli.add_command(uninstall.uninstall)
cli.add_command(plugin_cmd.plugin_list, name='plugin-list')


if __name__ == "__main__":
    cli()