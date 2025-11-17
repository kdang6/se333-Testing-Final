import csv
import os
from pathlib import Path

# Use relative path from repository root
repo_root = Path(__file__).resolve().parent.parent
p = repo_root / 'codebase' / 'target' / 'site' / 'jacoco' / 'jacoco.csv'
if not p.exists():
    print('MISSING', p)
    raise SystemExit(1)
with p.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    lm = lc = bm = bc = 0
    for row in r:
        lm += int(row.get('LINE_MISSED', 0) or 0)
        lc += int(row.get('LINE_COVERED', 0) or 0)
        bm += int(row.get('BRANCH_MISSED', 0) or 0)
        bc += int(row.get('BRANCH_COVERED', 0) or 0)
    lt = lm + lc
    bt = bm + bc
    if lt == 0 or bt == 0:
        print('EMPTY_TOTALS', lt, bt)
    else:
        print(f"LINE_MISSED={lm} LINE_COVERED={lc} LINE_TOTAL={lt} LINE_PCT={lc*100/lt:.2f}")
        print(f"BRANCH_MISSED={bm} BRANCH_COVERED={bc} BRANCH_TOTAL={bt} BRANCH_PCT={bc*100/bt:.2f}")
