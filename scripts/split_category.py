import pandas as pd

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data/StoreGoodsList_260218.CSV"
OUTPUT_PATH = BASE_DIR / "data/StoreGoodsList_260218_categorized.CSV"

try:
    df = pd.read_csv(INPUT_PATH, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(INPUT_PATH, encoding="cp949")

# 카테고리 컬럼을 > 구분자로 분리 (최대 3개)
split_cols = df["카테고리"].str.split(">", n=2, expand=True)
split_cols.columns = ["대분류", "중분류", "소분류"]

# 결측값 빈 문자열로 처리
split_cols = split_cols.fillna("")

# 기존 카테고리 컬럼 위치에 3개 컬럼 삽입
cat_idx = df.columns.get_loc("카테고리")
df = df.drop(columns=["카테고리"])

for i, col in enumerate(["대분류", "중분류", "소분류"]):
    df.insert(cat_idx + i, col, split_cols[col])

df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

# 검증 출력
print(f"총 행 수: {len(df)}")
print(f"대분류 고유값 수: {df['대분류'].nunique()}")
print(f"중분류 고유값 수: {df['중분류'].nunique()}")
print(f"소분류 고유값 수: {df['소분류'].nunique()}")
print(f"\n대분류 분포:\n{df['대분류'].value_counts()}")
print(f"\n빈 값 확인:")
print(f"  대분류 빈 값: {(df['대분류'] == '').sum()}")
print(f"  중분류 빈 값: {(df['중분류'] == '').sum()}")
print(f"  소분류 빈 값: {(df['소분류'] == '').sum()}")
print(f"\n샘플 5행:")
print(df[["대분류", "중분류", "소분류"]].head())
print(f"\n저장 완료: {OUTPUT_PATH}")
