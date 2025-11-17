import csv, os
repo_root = os.path.dirname(os.path.dirname(__file__))
csv_path = os.path.join(repo_root, 'codebase', 'target', 'site', 'jacoco', 'jacoco.csv')
if not os.path.exists(csv_path):
    print('jacoco.csv not found at', csv_path)
    raise SystemExit(1)
branch_missed = 0
branch_covered = 0
with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            bm = int(row['BRANCH_MISSED'])
            bc = int(row['BRANCH_COVERED'])
        except Exception:
            continue
        branch_missed += bm
        branch_covered += bc
total_branches = branch_missed + branch_covered
branch_cov = (branch_covered / total_branches * 100) if total_branches>0 else 0.0
print(f'Branch coverage: {branch_cov:.2f}% ({branch_covered} covered, {branch_missed} missed)')
print(f'Branches total: {total_branches}')