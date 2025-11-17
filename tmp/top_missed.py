import csv
from pathlib import Path
p = Path(r"C:/Users/Kenny/se333-testing-agent/codebase/target/site/jacoco/jacoco.csv")
if not p.exists():
    print('missing', p)
    raise SystemExit(1)
rows = []
with p.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        lm = int(row.get('LINE_MISSED') or 0)
        lc = int(row.get('LINE_COVERED') or 0)
        if lm>0:
            rows.append((lm, row.get('PACKAGE'), row.get('CLASS'), lc))
rows.sort(reverse=True)
print('Top 10 classes by missed lines:')
for lm, pkg, cls, lc in rows[:10]:
    print(f"{pkg}.{cls}: LINE_MISSED={lm} LINE_COVERED={lc}")
print('\nSummary counts:')
lm_sum = sum(r[0] for r in rows)
print('classes_with_missed =', len(rows))
