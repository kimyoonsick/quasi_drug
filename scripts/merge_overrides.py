"""process_csv.py 실행 후 수기 편집(오버라이드) 파일을 재적용하는 스크립트

프로모션명 기준으로 매칭하여 기존 행은 업데이트, 없는 행은 추가
"""
import csv
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

OVERRIDE_MAP = {
    "baropharm": os.path.join(DATA_DIR, "baropharm", "2604_baropharm-0 - 2604_baropharm.csv"),
    "saeropharm": os.path.join(DATA_DIR, "saeropharm", "2604_saeropharm_override.csv"),
    "platpharm": os.path.join(DATA_DIR, "platpharm", "2604_platpharm_override.csv"),
}

COLS_TO_UPDATE = ['분류', '일반/특별', '제휴사', '시작일', '종료일', '내용', '혜택', '카테고리', 'URL']


def merge_override(mall_name, override_path):
    base_file = os.path.join(DATA_DIR, f"2604_{mall_name}.csv")

    if not os.path.exists(base_file):
        print(f"  [{mall_name}] 기본 파일 없음: {base_file}")
        return
    if not os.path.exists(override_path):
        print(f"  [{mall_name}] 오버라이드 파일 없음: {override_path}")
        return

    # 오버라이드 파일 로드
    updates = {}
    update_order = []
    with open(override_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            promo = row.get('프로모션명', '').strip()
            if promo:
                updates[promo] = row
                update_order.append(promo)

    # 기본 파일 로드
    with open(base_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        base_rows = list(reader)
        fieldnames = reader.fieldnames

    # 기존 행 업데이트
    base_promos = set()
    updated_count = 0
    for row in base_rows:
        promo = row.get('프로모션명', '').strip()
        if promo:
            base_promos.add(promo)
            if promo in updates:
                upd = updates[promo]
                for col in COLS_TO_UPDATE:
                    if col in upd and col in fieldnames:
                        val = upd[col].strip() if upd[col] else ''
                        if val:
                            row[col] = val
                updated_count += 1

    # 오버라이드에만 있는 행 추가
    added_count = 0
    for promo in update_order:
        if promo not in base_promos:
            new_row = updates[promo]
            row_dict = {}
            for fn in fieldnames:
                row_dict[fn] = new_row.get(fn, '')
            base_rows.append(row_dict)
            added_count += 1

    # 저장
    with open(base_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(base_rows)

    print(f"  [{mall_name}] 완료 - 업데이트: {updated_count}건, 추가: {added_count}건")


def main():
    print("수기 편집 오버라이드 병합 시작")
    for mall_name, override_path in OVERRIDE_MAP.items():
        merge_override(mall_name, override_path)
    print("병합 완료")


if __name__ == "__main__":
    main()
