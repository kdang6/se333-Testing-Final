import csv
import os

repo_root = os.path.dirname(os.path.dirname(__file__))
csv_path = os.path.join(repo_root, 'codebase', 'target', 'site', 'jacoco', 'jacoco.csv')

if not os.path.exists(csv_path):
    print('jacoco.csv not found at', csv_path)
    raise SystemExit(1)

line_missed_total = 0
line_covered_total = 0
method_missed_total = 0
method_covered_total = 0
classes_with_missing_lines = []
classes_with_missing_methods = []

with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            line_missed = int(row['LINE_MISSED'])
            line_covered = int(row['LINE_COVERED'])
            method_missed = int(row['METHOD_MISSED'])
            method_covered = int(row['METHOD_COVERED'])
        except Exception as e:
            # skip header/invalid
            continue
        line_missed_total += line_missed
        line_covered_total += line_covered
        method_missed_total += method_missed
        method_covered_total += method_covered
        if line_missed > 0:
            classes_with_missing_lines.append((row['PACKAGE'] + '.' + row['CLASS'], line_missed, line_covered))
        if method_missed > 0:
            classes_with_missing_methods.append((row['PACKAGE'] + '.' + row['CLASS'], method_missed, method_covered))

total_lines = line_missed_total + line_covered_total
line_cov = (line_covered_total / total_lines * 100) if total_lines>0 else 0.0

print('JaCoCo CSV:', csv_path)
print('Total lines: ', total_lines)
print(f'Line coverage: {line_cov:.2f}% ({line_covered_total} covered, {line_missed_total} missed)')
print(f'Methods covered: {method_covered_total}, missed: {method_missed_total}')
print('\nClasses with missing lines (count: {})'.format(len(classes_with_missing_lines)))
for cls, missed, covered in sorted(classes_with_missing_lines, key=lambda x: -x[1])[:150]:
    print(f'- {cls}: lines missed={missed}, covered={covered}')

print('\nClasses with missing methods (count: {})'.format(len(classes_with_missing_methods)))
for cls, missed, covered in sorted(classes_with_missing_methods, key=lambda x: -x[1])[:150]:
    print(f'- {cls}: methods missed={missed}, covered={covered}')
