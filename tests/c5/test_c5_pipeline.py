#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / 'tests' / 'c5' / 'c5_matrix.json'

def main():
    data = json.loads(MATRIX.read_text())
    assert len(data['tests']) == 6
    ids = set()
    for item in data['tests']:
        assert item['id'] not in ids
        ids.add(item['id'])
        assert (ROOT / item['source']).exists()
        assert item['expected']
    subprocess.run([sys.executable, str(ROOT / 'tools' / 'c5_validate.py')], check=True, cwd=ROOT)
    print('C5 physical preparation pipeline: 6/6 PASS')

if __name__ == '__main__':
    main()
