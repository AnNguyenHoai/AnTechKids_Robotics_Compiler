#!/usr/bin/env python3
import time
import json
import yaml
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent


def load_benchmarks():
    config_file = Path(__file__).parent / "benchmarks.yaml"
    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['benchmarks']


def run_benchmark(benchmark):
    source = ROOT / benchmark['source']
    if not source.exists():
        return None

    # Đo thời gian compile
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(ROOT / "robot-compiler/main.py"), "--file", str(source)],
        capture_output=True,
        text=True
    )
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        return None

    # Đếm số instruction
    generated_header = ROOT / "robot-platform/main/src/Application/generated_program.h"
    instruction_count = 0
    if generated_header.exists():
        with open(generated_header, 'r', encoding='utf-8') as f:
            content = f.read()
            instruction_count = content.count("Instruction(")

    return {
        "name": benchmark['name'],
        "source": benchmark['source'],
        "compile_time": elapsed,
        "instruction_count": instruction_count,
        "success": True
    }


def run_all():
    benchmarks = load_benchmarks()
    results = []
    for bm in benchmarks:
        print(f"Running: {bm['name']} ...", end="")
        result = run_benchmark(bm)
        if result:
            print(f" OK ({result['compile_time']:.3f}s, {result['instruction_count']} instr)")
            results.append(result)
        else:
            print(" FAILED")
    return results


def save_history(results):
    history_dir = Path(__file__).parent / "history"
    history_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().isoformat()
    history_file = history_dir / f"{timestamp}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump({"timestamp": timestamp, "results": results}, f, indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true", help="Save results to history")
    args = parser.parse_args()

    results = run_all()
    if args.save and results:
        save_history(results)
        print(f"Saved history.")