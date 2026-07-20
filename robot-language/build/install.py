from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "generated"

DEST = (
    ROOT.parent /
    "robot-compiler" /
    "compiler" /
    "generated"
)

DEST.mkdir(
    parents=True,
    exist_ok=True
)

count = 0

for file in SOURCE.glob("*.py"):

    print("Copy:", file.name)

    shutil.copy2(
        file,
        DEST / file.name
    )

    count += 1

print("Copied", count, "files")

print()

print("Artifacts installed")

print()