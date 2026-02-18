import csv
import re
from pathlib import Path


def extract_products(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    products = []
    blocks = re.split(r'<div\s+id="(\d{10,})"', content)

    for i in range(1, len(blocks), 2):
        prod_id = blocks[i]
        block = blocks[i + 1] if i + 1 < len(blocks) else ''

        name_m = re.search(r'class="title-18-medium[^"]*"[^>]*title="([^"]+)"', block)
        if not name_m:
            continue

        spec_m = re.search(
            r'<span\s+class="title-16-medium[^"]*text-neutral-30[^"]*"[^>]*>([^<]+)</span>',
            block
        )

        price_m = re.search(
            r'<div\s+class="text-\[20px\]\s+font-bold"[^>]*>([^<]+)</div>',
            block
        )
        if not price_m:
            continue

        products.append({
            'id': prod_id,
            'name': name_m.group(1).strip(),
            'spec': spec_m.group(1).strip() if spec_m else '',
            'price': int(re.sub(r'[^\d]', '', price_m.group(1).strip()))
        })

    return products


def norm(text):
    return re.sub(r'\s+', '', text.strip()) if text else ''


def main():
    base_dir = Path(__file__).parent

    # HTML에서 상품 추출 + 중복 ID 제거
    all_products = []
    seen_ids = set()
    for i in range(1, 8):
        f = base_dir / f'거즈붕대탈지면{i}.html'
        if not f.exists():
            continue
        for p in extract_products(f):
            if p['id'] not in seen_ids:
                seen_ids.add(p['id'])
                all_products.append(p)

    # 매핑 딕셔너리
    name_price_map = {}
    name_only_map = {}
    for p in all_products:
        key = (norm(p['name']), p['price'])
        if key not in name_price_map:
            name_price_map[key] = p['id']
        name_only_map.setdefault(norm(p['name']), []).append(p['id'])

    # CSV 읽기
    csv_path = base_dir / 'platpharm_260218.csv'
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            rows.append(row)

    header = rows[0][:5]
    data_rows = [row[:5] for row in rows[1:]]

    # 노이즈 제거 + 중복 제거 + 상품코드 매핑
    new_rows = [header + ['상품코드']]
    seen = set()

    for row in data_rows:
        if len(row) < 4:
            continue
        cat, name, spec, price_str, *_ = row

        if name in ['재고', '상품 더 담기'] or name.startswith('업체별'):
            continue

        try:
            price = int(re.sub(r'[^\d]', '', price_str))
        except (ValueError, TypeError):
            continue

        n = norm(name)
        dedup = (n, norm(spec), price)
        if dedup in seen:
            continue
        seen.add(dedup)

        code = name_price_map.get((n, price), '')
        if not code and n in name_only_map and len(name_only_map[n]) == 1:
            code = name_only_map[n][0]

        new_rows.append(row + [code])

    # HTML에 있지만 CSV에 없는 상품 추가
    for p in all_products:
        dedup = (norm(p['name']), norm(p['spec']), p['price'])
        if dedup not in seen:
            new_rows.append(['거즈/붕대/탈지면', p['name'], p['spec'], str(p['price']), 'platpharm', p['id']])
            seen.add(dedup)

    # 저장
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerows(new_rows)

    total = len(new_rows) - 1
    with_code = sum(1 for r in new_rows[1:] if len(r) > 5 and r[5])
    print(f'완료: {total}개 상품, {with_code}개 상품코드 매핑')


if __name__ == '__main__':
    main()
