"""RSD-22 release contract consolidation regression suite."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "RSD-22_RELEASE_CONTRACT_CONSOLIDATION.md"

LEGACY_DOCS = {
    "RSD-16_CLEAN_MACHINE_RELEASE_ACCEPTANCE.md",
    "RSD-17_PRODUCTION_DISTRIBUTION_BUILDER.md",
    "RSD-20-P_PRODUCTION_PORTABLE_RELEASE_PROOF.md",
    "RSD-20-P1_PRODUCTION_RELEASE_ARTIFACT_ASSEMBLY.md",
    "RSD-21.6_PRODUCTION_RELEASE_LAUNCHER.md",
    "RSD-21.8_REAL_ROBOSTUDIO_COMPILER_CONTRACT.md",
}


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    text = CONTRACT.read_text(encoding="utf-8")

    required_sections = [
        "## 2. Authority",
        "## 3. Production release artifact",
        "## 4. Source-of-truth and path rules",
        "## 5. Toolchain boundary",
        "## 6. Application boundary",
        "## 7. Launcher contract",
        "## 8. Compiler contract",
        "## 9. Release pipeline",
        "## 10. Evidence requirements",
        "## 11. Clean-machine definition",
        "## 12. Fail-closed rules",
        "## 13. Ownership matrix",
        "## 14. Supersession rule",
    ]
    for section in required_sections:
        check(f"canonical contract contains {section}", section in text)

    required_invariants = [
        "The ZIP is the unit that is copied to another machine.",
        "never discover production dependencies through `PATH`",
        "never use the caller's current working directory as an implicit release root",
        "never depend on a developer virtual environment",
        "never embed the developer checkout path into the shipped artifact",
        "RSD-23",
        "RSD-24",
        "H28",
        "compiler/robostudio_bridge.py",
        "RoboStudio.cmd",
        "%~dp0",
        "RSD-20-P.1 production artifact assembly",
    ]
    for invariant in required_invariants:
        check(f"canonical contract contains invariant: {invariant}", invariant in text)

    check(
        "current external Python/PlatformIO boundary is explicitly classified",
        "current RoboStudio production distribution implementation packages the" in text
        and "Python and PlatformIO as target machine prerequisites" in text,
    )
    check(
        "final zero-development-machine target is explicit",
        "without installing a developer Python/PlatformIO environment or cloning the repository" in text,
    )

    for filename in LEGACY_DOCS:
        path = ROOT / filename
        if not path.is_file():
            continue
        legacy = path.read_text(encoding="utf-8")
        check(f"legacy release document defers to RSD-22: {filename}", "RSD-22" in legacy)

    print("RSD-22 release contract consolidation checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
