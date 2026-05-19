import csv
import json
import shutil
from pathlib import Path

csv_path   = Path(r'data/baropharm/products/2605_baropharm_products.csv')
backup_path = Path(r'data/baropharm/products/2605_baropharm_products.bak.csv')
brand_path  = Path(r'data/baropharm/products/2605_baropharm_products_brand.csv')
dict_path   = Path(r'data/baropharm/products/260519_바로팜_상품카테고리사전.json')
tmp_path    = Path(r'data/baropharm/products/2605_baropharm_products.tmp.csv')

# ── 1. 백업
shutil.copy2(csv_path, backup_path)
print(f"백업 완료: {backup_path}")

# ── 2. 브랜드 store_id 수집
brand_ids = set()
with open(brand_path, encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        brand_ids.add(row['store_id'])
print(f"브랜드 store_id {len(brand_ids)}개 로드")

# ── 3. 역방향 조회 테이블: 소분류 -> 카테고리
with open(dict_path, encoding='utf-8') as f:
    cat_dict = json.load(f)

sub_to_cat = {}
for cat, subs in cat_dict.items():
    for sub in subs:
        sub_to_cat[sub] = cat
print(f"사전 소분류 항목 {len(sub_to_cat)}개 로드")

# ── 4. 매핑 규칙
# 상품카테고리가 이 값들 중 하나인 브랜드 행 → 재매핑 대상
TARGET_CATS = {
    '건강관리', '건기식 및 일반의약품', '교양서적', '분쇄기', '뷰티',
    '브랜드관', '약국용품', '의료용품', '전체', '캠핑', '코스메슈티컬', '홍보용품',
    '',  # 빈 카테고리도 처리
}

KPAI_EXCEPTIONS = {
    '[KPAI] 맞춤 OTC 선택가이드',
    '[KPAI]KPAI 톡톡 일반약 실전 노하우',
}

EXTRA_MAP = {
    '건강관리':           '건강식품',
    '건기식 및 일반의약품': '일반의약품',   # KPAI 예외는 별도 처리 → 교양서적
    '교양서적':           '의약외상품',
    '분쇄기':             '약국용품',
    '뷰티':               '화장품',
    '약국용품':           '약국용품',
    '의료용품':           '의약외상품',
    '캠핑':               '스포츠/레저',
    '코스메슈티컬':       '화장품',
    '홍보용품':           '약국용품',
}

def resolve_category(row):
    """상품소분류 기반으로 상품카테고리 결정"""
    sub  = row.get('상품소분류', '').strip()
    name = row.get('상품명', '').strip()
    cat1 = row.get('카테고리1', '').strip()

    # 1) 사전 직접 매핑 (소분류 → 카테고리)
    if sub in sub_to_cat:
        return sub_to_cat[sub]

    # 2) 브랜드관 / 전체 → 카테고리1 값
    if sub in ('브랜드관', '전체'):
        return cat1 if cat1 else ''

    # 3) KPAI 예외 (건기식 및 일반의약품 중 특정 상품명 → 교양서적)
    if sub == '건기식 및 일반의약품' and name in KPAI_EXCEPTIONS:
        return '교양서적'

    # 4) 기타 추가 매핑
    if sub in EXTRA_MAP:
        return EXTRA_MAP[sub]

    # 5) 소분류가 비어있으면 카테고리1을 fallback으로 사용
    if not sub and cat1:
        return cat1

    return ''


# ── 5. 메인 처리
rows_in = 0
rows_out = 0
rows_deleted = 0
updated_count = 0
unmapped = {}

with open(csv_path, encoding='utf-8-sig', newline='') as fin, \
     open(tmp_path, 'w', encoding='utf-8-sig', newline='') as fout:

    reader = csv.DictReader(fin)
    fieldnames = [f for f in reader.fieldnames if f is not None]
    writer = csv.DictWriter(fout, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for row in reader:
        rows_in += 1
        is_brand = row['store_id'] in brand_ids
        old_cat  = row.get('상품카테고리', '').strip()

        # 브랜드 행이고, 현재 카테고리가 재매핑 대상일 때만 업데이트
        if is_brand and old_cat in TARGET_CATS:
            new_cat = resolve_category(row)
            if new_cat != old_cat:
                updated_count += 1
            row['상품카테고리'] = new_cat

            if not new_cat:
                sub = row.get('상품소분류', '').strip()
                unmapped[sub] = unmapped.get(sub, 0) + 1

        # 일반의약품 행 삭제 (brand/mall 불문)
        if row.get('상품카테고리', '').strip() == '일반의약품':
            rows_deleted += 1
            continue

        writer.writerow(row)
        rows_out += 1

# ── 6. tmp → csv 교체
shutil.move(str(tmp_path), str(csv_path))

print(f"\n처리 완료")
print(f"  원본 행 수    : {rows_in:,}")
print(f"  업데이트 행 수: {updated_count:,}")
print(f"  삭제 행 수    : {rows_deleted:,} (일반의약품)")
print(f"  최종 행 수    : {rows_out:,}")
if unmapped:
    print(f"\n  [경고] 매핑 실패 소분류 ({sum(unmapped.values())}행):")
    for sub, cnt in sorted(unmapped.items(), key=lambda x: -x[1]):
        print(f"    {sub!r}: {cnt}행")
else:
    print("  [OK] 미매핑 소분류 없음")
