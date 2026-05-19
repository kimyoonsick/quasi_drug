import csv
import shutil
from pathlib import Path

brand_path = Path(r'data/baropharm/products/2605_baropharm_products_brand.csv')
main_path = Path(r'data/baropharm/products/2605_baropharm_products.csv')
tmp_path = Path(r'data/baropharm/products/2605_baropharm_products.tmp.csv')

# Load brand data
brand_data = {}
with open(brand_path, encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        key = (row['store_id'], row['상품명'], row['가격'])
        brand_data[key] = row

store_ids = set([k[0] for k in brand_data.keys()])

updated_count = 0
missed_count = 0

with open(main_path, encoding='utf-8-sig', newline='') as fin, \
     open(tmp_path, 'w', encoding='utf-8-sig', newline='') as fout:
    
    reader = csv.DictReader(fin)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(fout, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for row in reader:
        if row['store_id'] in store_ids:
            key = (row['store_id'], row['상품명'], row['가격'])
            if key in brand_data:
                b_row = brand_data[key]
                # Update specific columns
                cols_to_update = ['상품카테고리', '상품소분류', '규격', '단위수량', '단위', '할인율', '가격', '할인전가격', '포인트백']
                for col in cols_to_update:
                    if col in b_row:
                        row[col] = b_row[col]
                updated_count += 1
            else:
                missed_count += 1
                print(f"Missed matching: {key}")
        writer.writerow(row)

# Replace main file with tmp file
shutil.move(str(tmp_path), str(main_path))

print(f"Update complete. Updated: {updated_count}, Missed: {missed_count}")
