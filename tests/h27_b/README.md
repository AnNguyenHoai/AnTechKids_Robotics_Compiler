# H27-B standalone entrypoint regression

The RoboStudio GUI is expected to be launchable from the `robostudio` directory with `python main.py`. The entrypoint must add the repository root to `sys.path` before importing services that depend on shared modules under `tools/`.
