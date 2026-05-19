"""
메인 CSV의 상품카테고리를 사전파일 기준으로 매핑
- 상품소분류 값을 key로 JSON 사전 조회
- 매칭되면 상품카테고리에 value 설정
- 매칭 안되면 상품카테고리 그대로 유지
- 다른 컬럼은 일절 변경 없음
"""
import csv, json
from pathlib import Path

data_dir = Path(r'd:\Users\Desktop\pico\quasi_drug\data\baropharm\products')
main_csv = data_dir / '2605_baropharm_products.csv'
dict_json = data_dir / '260519_바로팜_상품카테고리사전.json'

# 사전 로드
with open(dict_json, encoding='utf-8') as f:
    cat_dict = json.load(f)
print(f'사전 항목: {len(cat_dict)}개')

# CSV 읽기
with open(main_csv, encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    header = reader.fieldnames
    rows = list(reader)
print(f'총 행: {len(rows)}')

# 매핑
mapped = 0
not_mapped = 0
unmapped_values = set()

for row in rows:
    sub = row.get('상품소분류', '').strip()
    if sub in cat_dict:
        row['상품카테고리'] = cat_dict[sub]
        mapped += 1
    else:
        if sub:
            unmapped_values.add(sub)
        not_mapped += 1

print(f'매핑됨: {mapped}행')
print(f'미매핑: {not_mapped}행')
if unmapped_values:
    samples = sorted(unmapped_values)[:20]
    print(f'미매핑 상품소분류 샘플 ({len(unmapped_values)}종): {samples}')

# 저장
with open(main_csv, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
print(f'\n저장 완료: {main_csv.name}')

# 검증
print('\n== 검증 (brand 샘플) ==')
with open(main_csv, encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 3:
            break
        print(f'  상품카테고리={row["상품카테고리"]!r}, 상품소분류={row["상품소분류"]!r}')
