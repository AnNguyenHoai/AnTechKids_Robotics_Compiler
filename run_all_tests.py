#!/usr/bin/env python3
"""Run the repository's regression and RSD contract test suites."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def _configure_utf8_output() -> None:
    os.environ["PYTHONUTF8"]="1"
    os.environ["PYTHONIOENCODING"]="utf-8"
    for stream in (sys.stdout,sys.stderr):
        reconfigure=getattr(stream,"reconfigure",None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8",errors="strict")


def _child_environment() -> dict[str,str]:
    env=os.environ.copy()
    env["PYTHONUTF8"]="1"
    env["PYTHONIOENCODING"]="utf-8"
    root=str(ROOT)
    existing=env.get("PYTHONPATH")
    env["PYTHONPATH"]=root if not existing else root+os.pathsep+existing
    return env


def run_script(path:Path)->bool:
    print(f"\n=== Running {path.relative_to(ROOT)} ===")
    result=subprocess.run([sys.executable,str(path)],cwd=ROOT,text=True,env=_child_environment())
    if result.returncode!=0:
        print(f"FAILED: {path.relative_to(ROOT)} (exit {result.returncode})",file=sys.stderr)
        return False
    print(f"PASS: {path.relative_to(ROOT)}")
    return True


def main()->int:
    _configure_utf8_output()
    tests=[ROOT/"robot-compiler"/"tests"/"run_tests.py",ROOT/"robot-frontend-robosim"/"test"/"run_tests.py",ROOT/"robot-compiler"/"integration"/"end_to_end"/"run_integration_tests.py",ROOT/"tests"/"c4"/"test_language_semantics.py",ROOT/"tests"/"c5"/"test_c5_pipeline.py"]
    for name in ["rsd_02","rsd_03","rsd_04","rsd_05","rsd_06","rsd_07","rsd_08","rsd_09","rsd_10","rsd_11","rsd_12","rsd_13","rsd_14","rsd_15","rsd_16","rsd_17","rsd_18","rsd_19","rsd_20_p","rsd_20_p1","rsd_20","rsd_21","rsd_21_2","rsd_21_3","rsd_21_4","rsd_21_5","rsd_21_6","rsd_21_7","rsd_21_8"]:tests.append(ROOT/"tests"/name/f"run_{name}.py")
    tests.append(ROOT/"tests"/"b2_2"/"run_b2_2.py")
    tests.append(ROOT/"tests"/"b2_2"/"run_portable_child_closure.py")
    tests.append(ROOT/"tests"/"b2_3"/"run_b2_3.py")
    for name in ["h26_a","h26_b","h26_c","h26_d","h26_e","h26_f","h26_g","h26_h","h26_i","h26_j","h26_k","h26_l","h26_m","h26_ota","h26_o","h27_a1","h27_b0","h27_b","h28_b","h29_a","h29_b","h29_c","h29_d"]:tests.append(ROOT/"tests"/name/f"run_{name}.py")
    missing=[p.relative_to(ROOT) for p in tests if not p.exists()]
    if missing:
        print("Missing required test runner(s):",file=sys.stderr)
        [print(f"  - {p}",file=sys.stderr) for p in missing]
        return 2
    for test in tests:
        if not run_script(test):
            return 1
    print("\nALL TESTS PASSED")
    return 0

if __name__=="__main__":raise SystemExit(main())
