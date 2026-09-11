"""Package application-owned runtime resources for a RoboStudio release."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from tools.runtime_resources import RESOURCE_SPECS, write_resource_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "packages"


def package_resources(source: Path, output: Path) -> dict:
    """Copy declared runtime resources and emit a relocatable manifest."""
    source = Path(source)
    output = Path(output)
    if not source.is_dir():
        raise RuntimeError(f"Runtime resource source directory not found: {source}")
    if output == source or source in output.parents:
        raise RuntimeError("Output resource directory must not be inside the source directory.")

    output.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name, relative in RESOURCE_SPECS.items():
        source_file = source / relative
        if not source_file.is_file():
            raise RuntimeError(f"Required runtime resource is missing: {source_file}")
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
        copied.append(name)

    manifest_path = write_resource_manifest(output, copied)
    return {"resources": copied, "manifest": str(manifest_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Package RoboStudio runtime resources")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Repository resource source root")
    parser.add_argument("--output", type=Path, required=True, help="runtime/resources output directory")
    args = parser.parse_args()
    result = package_resources(args.source, args.output)
    print(f"Runtime resources staged: {args.output}")
    print(f"Resources copied: {', '.join(result['resources'])}")
    print(f"Manifest: {result['manifest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
