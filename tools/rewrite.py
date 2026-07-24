#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "robot-frontend-robosim"))

from frontend import rewrite
import argparse

def main():
    parser = argparse.ArgumentParser(description="Rewrite RoboSim source to Standard Robot API")
    parser.add_argument("--input", required=True, help="Input .py file (RoboSim)")
    parser.add_argument("--output", required=True, help="Output .rewrite.py file")
    args = parser.parse_args()
    rewrite(Path(args.input), Path(args.output))
    print(f"Rewritten to {args.output}")

if __name__ == "__main__":
    main()