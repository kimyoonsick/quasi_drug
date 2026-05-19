import csv
import shutil
from pathlib import Path

csv_path = Path('data/baropharm/products/2605_baropharm_products.csv')
tmp_path = Path('data/baropharm/products/2605_baropharm_products.tmp.csv')

fixed_count = 0
total_count = 0

with open(csv_path, encoding='utf-8-sig', newline='') as fin, \
     open(tmp_path, 'w', encoding='utf-8-sig', newline='') as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)
    
    header = next(reader)
    writer.writerow(header)
    
    for row in reader:
        total_count += 1
        # Check if the row has 15 columns, which implies '포인트백' is missing and columns shifted
        if len(row) == 15 and row[13] in ('True', 'False') and row[14].startswith('202'):
            row.insert(13, '')
            fixed_count += 1
        writer.writerow(row)

print(f"Total rows: {total_count}")
print(f"Fixed rows: {fixed_count}")

shutil.move(str(tmp_path), str(csv_path))
