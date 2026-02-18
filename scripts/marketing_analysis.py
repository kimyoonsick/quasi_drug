import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data/StoreGoodsList_260218_categorized.CSV"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

today = datetime.now().strftime("%y%m%d")
OUTPUT_PATH = OUTPUT_DIR / f"marketing_analysis_{today}.md"

try:
    df = pd.read_csv(INPUT_PATH, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(INPUT_PATH, encoding="cp949")

unique_products = df.drop_duplicates(subset="마스터코드")

lines = []
w = lines.append

# ================================================================
#  Step 1: 각 전문가 초안
# ================================================================
w("# 의약외품 쇼핑몰 마케팅 분석 리포트\n")

w("## Step 1: 전문가별 초안\n")

# [Dr. Stats]
w("### [Dr. Stats] 통계수학자 관점\n")

w("#### (1) 기초 통계 개요\n")
w(f"- 총 레코드 수 (공급사별 상품): {len(df):,}")
w(f"- 고유 상품 수 (마스터코드 기준): {df['마스터코드'].nunique():,}")
w(f"- 중분류 수: {df['중분류'].nunique()}")
w(f"- 소분류 수: {df['소분류'].nunique()}")
w(f"- 제조사 수: {df['제조사'].nunique():,}")
w(f"- 공급사 수: {df['공급사'].nunique():,}\n")

w("#### (2) 가격 분포 기술통계 (일반가, 원)\n")
price_stats = df["일반가"].describe()
w(f"- 평균: {price_stats['mean']:,.0f}")
w(f"- 중앙값: {price_stats['50%']:,.0f}")
w(f"- 표준편차: {price_stats['std']:,.0f}")
w(f"- 최솟값: {price_stats['min']:,.0f}")
w(f"- 최댓값: {price_stats['max']:,.0f}")
w(f"- 왜도(skewness): {df['일반가'].skew():.2f}")
w(f"- 첨도(kurtosis): {df['일반가'].kurtosis():.2f}\n")

w("#### (3) 중분류별 상품 집중도 (HHI)\n")
cat_shares = df.groupby("중분류").size() / len(df)
hhi = (cat_shares ** 2).sum()
w(f"- HHI: {hhi:.4f} (0에 가까울수록 분산, 1에 가까울수록 집중)")
top3_cat = cat_shares.nlargest(3)
w("- 상위 3 중분류 점유율:")
for cat, share in top3_cat.items():
    w(f"  - {cat}: {share:.1%}")
w("")

w("#### (4) 공급사별 상품 공급 집중도 (HHI)\n")
sup_shares = df.groupby("공급사").size() / len(df)
sup_hhi = (sup_shares ** 2).sum()
w(f"- HHI: {sup_hhi:.4f}")
top5_sup = sup_shares.nlargest(5)
w("- 상위 5 공급사 점유율:")
for sup, share in top5_sup.items():
    w(f"  - {sup}: {share:.1%}")
w("")

w("#### (5) 동일 상품(마스터코드) 공급사 간 가격 변동계수(CV)\n")
price_cv = df.groupby("마스터코드")["일반가"].agg(["mean", "std", "count"])
price_cv = price_cv[price_cv["count"] >= 3]
price_cv["cv"] = price_cv["std"] / price_cv["mean"]
price_cv = price_cv.dropna()
if len(price_cv) > 0:
    high_cv = price_cv.nlargest(10, "cv")
    w(f"- 분석 대상 상품 수 (공급사 3곳 이상): {len(price_cv):,}")
    w(f"- 평균 CV: {price_cv['cv'].mean():.4f}")
    w("- CV 최대 상위 10개 상품:\n")
    w("| 마스터코드 | 상품명 | CV | 평균가 | 공급사수 |")
    w("|---|---|---|---|---|")
    for idx, row in high_cv.iterrows():
        name = df[df["마스터코드"] == idx]["상품명"].iloc[0][:30]
        w(f"| {idx} | {name} | {row['cv']:.3f} | {row['mean']:,.0f} | {int(row['count'])} |")
    w("")

# [Senior Analyst]
w("### [Senior Analyst] 데이터 분석가 관점\n")

w("#### (1) 중분류별 상품 구성 현황 (고유 상품 기준)\n")
mid_cat = unique_products.groupby("중분류").agg(
    고유상품수=("마스터코드", "count"),
    평균가=("일반가", "mean"),
    전시Y비율=("전시상태", lambda x: (x == "Y").mean()),
).sort_values("고유상품수", ascending=False)
w("| 중분류 | 상품수 | 평균가 | 전시율 |")
w("|---|---|---|---|")
for cat, row in mid_cat.iterrows():
    w(f"| {cat} | {int(row['고유상품수']):,} | {row['평균가']:,.0f} | {row['전시Y비율']:.1%} |")
w("")

w("#### (2) 소분류별 TOP 10 (레코드 수 = 공급사 경쟁 격렬)\n")
sub_cat = df.groupby(["중분류", "소분류"]).agg(
    레코드수=("일련번호", "count"),
    고유상품수=("마스터코드", "nunique"),
    공급사수=("공급사", "nunique"),
    평균가=("일반가", "mean"),
).sort_values("레코드수", ascending=False).head(10)
w("| 중분류 | 소분류 | 레코드 | 상품 | 공급사 | 평균가 |")
w("|---|---|---|---|---|---|")
for (mid, sub), row in sub_cat.iterrows():
    w(f"| {mid} | {sub} | {int(row['레코드수']):,} | {int(row['고유상품수'])} | {int(row['공급사수'])} | {row['평균가']:,.0f} |")
w("")

w("#### (3) 전시 상태 분석\n")
display_y = (df["전시상태"] == "Y").sum()
display_n = (df["전시상태"] == "N").sum()
w(f"- 전시중(Y): {display_y:,} ({display_y/len(df):.1%})")
w(f"- 미전시(N): {display_n:,} ({display_n/len(df):.1%})\n")

w("#### (4) 재고 현황\n")
zero_stock = (df["재고"] == 0).sum()
low_stock = ((df["재고"] > 0) & (df["재고"] <= 100)).sum()
w(f"- 재고 0: {zero_stock:,}건 ({zero_stock/len(df):.1%})")
w(f"- 재고 1~100: {low_stock:,}건 ({low_stock/len(df):.1%})")
w(f"- 재고 100 초과: {len(df) - zero_stock - low_stock:,}건\n")

w("#### (5) 과세/면세 비율\n")
tax = df["면세/과세"].value_counts()
for t, cnt in tax.items():
    w(f"- {t}: {cnt:,} ({cnt/len(df):.1%})")
w("")

# [Mall Marketer]
w("### [Mall Marketer] 제약 쇼핑몰 마케터 관점\n")

w("#### (1) 카테고리별 마케팅 매력도 (상품 다양성 x 공급사 경쟁)\n")
attractiveness = df.groupby("중분류").agg(
    상품다양성=("마스터코드", "nunique"),
    공급사수=("공급사", "nunique"),
    평균가=("일반가", "mean"),
    전시율=("전시상태", lambda x: (x == "Y").mean()),
    재고보유율=("재고", lambda x: (x > 0).mean()),
)
attractiveness["매력도점수"] = (
    attractiveness["상품다양성"].rank(pct=True) * 0.3
    + attractiveness["공급사수"].rank(pct=True) * 0.2
    + attractiveness["전시율"].rank(pct=True) * 0.25
    + attractiveness["재고보유율"].rank(pct=True) * 0.25
) * 100
attractiveness = attractiveness.sort_values("매력도점수", ascending=False)
w("| 중분류 | 상품수 | 공급사 | 평균가 | 전시율 | 재고율 | 점수 |")
w("|---|---|---|---|---|---|---|")
for cat, row in attractiveness.iterrows():
    w(f"| {cat} | {int(row['상품다양성'])} | {int(row['공급사수'])} | {row['평균가']:,.0f} | {row['전시율']:.0%} | {row['재고보유율']:.0%} | {row['매력도점수']:.1f} |")
w("")

w("#### (2) 가격 경쟁력 분석 (동일 상품 최저가 vs 최고가)\n")
price_range = df.groupby("마스터코드").agg(
    최저가=("일반가", "min"),
    최고가=("일반가", "max"),
    공급사수=("공급사", "nunique"),
)
price_range = price_range[price_range["공급사수"] >= 3]
price_range["가격차이율"] = (price_range["최고가"] - price_range["최저가"]) / price_range["최저가"]
price_range = price_range[price_range["최저가"] > 0]
big_gap = price_range.nlargest(10, "가격차이율")
w("동일 상품 가격 차이율 TOP 10 (공급사 3곳 이상):\n")
w("| 상품명 | 최저가 | 최고가 | 차이율 | 공급사 |")
w("|---|---|---|---|---|")
for idx, row in big_gap.iterrows():
    name = df[df["마스터코드"] == idx]["상품명"].iloc[0][:35]
    w(f"| {name} | {int(row['최저가']):,} | {int(row['최고가']):,} | {row['가격차이율']:.0%} | {int(row['공급사수'])} |")
w("")

w("#### (3) 공급사별 독점 상품 분석\n")
product_supplier_count = df.groupby("마스터코드")["공급사"].nunique()
exclusive_products = product_supplier_count[product_supplier_count == 1].index
exclusive_by_supplier = df[df["마스터코드"].isin(exclusive_products)].groupby("공급사")["마스터코드"].nunique()
exclusive_by_supplier = exclusive_by_supplier.sort_values(ascending=False).head(10)
w("독점 상품(공급사 1곳) 보유 TOP 10:\n")
w("| 공급사 | 독점 상품수 |")
w("|---|---|")
for sup, cnt in exclusive_by_supplier.items():
    w(f"| {sup} | {cnt} |")
w("")

w("#### (4) 반품 가능 기한 분포\n")
return_dist = df["반품가능기한"].value_counts().sort_index()
w("| 기한 | 건수 | 비율 |")
w("|---|---|---|")
for period, cnt in return_dist.items():
    w(f"| {period} | {cnt:,} | {cnt/len(df):.1%} |")
w("")


# ================================================================
#  Step 2: 상호 비판 및 보완
# ================================================================
w("## Step 2: 상호 비판 및 보완\n")

w("### Dr. Stats → Senior Analyst\n")
w("- 전시율/재고율을 단순 비율로 제시하나, 중분류 간 표본 크기 차이로 비율의 신뢰구간이 상이함. 소규모 카테고리의 전시율은 불안정")
w("- 매력도점수의 가중치(0.3/0.2/0.25/0.25)에 대한 근거가 필요\n")

w("### Dr. Stats → Mall Marketer\n")
w("- 가격차이율을 최저가 대비로 계산하나, 최저가가 극단적으로 낮은 이상치일 경우 차이율이 왜곡됨. 중앙값 대비가 더 강건")
w("- 독점 상품 분석에 '실제 판매력' 지표가 결여됨\n")

w("### Senior Analyst → Dr. Stats\n")
w("- HHI는 학술적이나 현업에서 직관적이지 않음. '상위 N개 카테고리가 전체의 X% 차지' 형태가 더 액셔너블")
w("- CV 분석은 유용하나, 가격 이상치 필터링이 선행되어야 함\n")

w("### Mall Marketer → Dr. Stats\n")
w("- 왜도/첨도 등 분포 지표는 마케팅 의사결정에 직접 쓰이지 않음. 가격 구간별 상품 비중이 프로모션 기획에 더 실용적")
w("- 가격 CV보다 '최저가 공급사 선택 시 절감 가능 금액'이 KPI에 가까움\n")

w("### Mall Marketer → Senior Analyst\n")
w("- 소분류 TOP 10이 레코드 수(공급사 중복) 기준이라 실제 '고객이 찾는 카테고리'와 괴리가 있을 수 있음")
w("- 전시 상태 분석에 '전시 가능한데 미전시' 여부 구분이 필요\n")


# ================================================================
#  Step 3: 최종 합의안
# ================================================================
w("## Step 3: 최종 합의안 - 마케팅 액션 인사이트\n")

w("### (1) 쇼핑몰 상품 구성 핵심 지표\n")
avg_suppliers = df.groupby("마스터코드")["공급사"].nunique().mean()
w(f"- 고유 상품(마스터코드): {df['마스터코드'].nunique():,}개")
w(f"- 총 SKU(공급사별): {len(df):,}개")
w(f"- 중분류: {df['중분류'].nunique()}개 / 소분류: {df['소분류'].nunique()}개")
w(f"- 참여 공급사: {df['공급사'].nunique():,}곳")
w(f"- 참여 제조사: {df['제조사'].nunique():,}곳")
w(f"- 상품당 평균 공급사: {avg_suppliers:.1f}곳\n")

w("### (2) 가격대별 상품 분포 (프로모션 기획용)\n")
bins = [0, 1000, 3000, 5000, 10000, 30000, 50000, 100000, float("inf")]
labels = ["~1천", "1~3천", "3~5천", "5천~1만", "1~3만", "3~5만", "5~10만", "10만~"]
df["가격대"] = pd.cut(df["일반가"], bins=bins, labels=labels, right=True)
price_band = df["가격대"].value_counts().sort_index()
w("| 가격대 | 건수 | 비율 | 누적 |")
w("|---|---|---|---|")
cumsum = 0
for band, cnt in price_band.items():
    cumsum += cnt / len(df)
    w(f"| {band} | {cnt:,} | {cnt/len(df):.1%} | {cumsum:.1%} |")
w("")

w("### (3) 중분류별 종합 마케팅 분석 (합의 기준)\n")
final = df.groupby("중분류").agg(
    고유상품=("마스터코드", "nunique"),
    총SKU=("일련번호", "count"),
    공급사수=("공급사", "nunique"),
    평균가=("일반가", "mean"),
    중앙가=("일반가", "median"),
    전시율=("전시상태", lambda x: (x == "Y").mean()),
    재고보유율=("재고", lambda x: (x > 0).mean()),
    평균재고=("재고", "mean"),
).sort_values("고유상품", ascending=False)
w("| 중분류 | 상품 | SKU | 공급사 | 평균가 | 중앙가 | 전시율 | 재고율 |")
w("|---|---|---|---|---|---|---|---|")
for cat, row in final.iterrows():
    w(f"| {cat} | {int(row['고유상품'])} | {int(row['총SKU']):,} | {int(row['공급사수'])} | {row['평균가']:,.0f} | {row['중앙가']:,.0f} | {row['전시율']:.0%} | {row['재고보유율']:.0%} |")
w("")

w("### (4) 최저가 공급사 전환 시 절감 가능 분석\n")
savings = df.groupby("마스터코드").agg(
    최저가=("일반가", "min"),
    최고가=("일반가", "max"),
    중앙가=("일반가", "median"),
    공급사수=("공급사", "nunique"),
)
savings = savings[savings["공급사수"] >= 2]
savings["절감가능액"] = savings["중앙가"] - savings["최저가"]
total_potential = savings["절감가능액"].sum()
avg_saving = savings["절감가능액"].mean()
w(f"- 분석 대상: 공급사 2곳 이상 상품 {len(savings):,}개")
w(f"- 상품당 평균 절감 가능액(중앙가-최저가): {avg_saving:,.0f}원")
w(f"- 전체 절감 가능 총액: {total_potential:,.0f}원\n")

w("### (5) 전시 최적화 기회 (재고 있으나 미전시)\n")
has_stock_not_displayed = df[(df["재고"] > 0) & (df["전시상태"] == "N")]
w(f"- 재고 보유 & 미전시 SKU: {len(has_stock_not_displayed):,}건\n")
opportunity_by_cat = has_stock_not_displayed.groupby("중분류").size().sort_values(ascending=False).head(10)
w("중분류별 기회 TOP 10:\n")
w("| 중분류 | 건수 |")
w("|---|---|")
for cat, cnt in opportunity_by_cat.items():
    w(f"| {cat} | {cnt:,} |")
w("")

w("### (6) 공급사 의존도 리스크 분석\n")
supplier_product_share = df.groupby("공급사")["마스터코드"].nunique()
total_unique = df["마스터코드"].nunique()
top_suppliers = supplier_product_share.nlargest(10)
w("상위 10 공급사 (고유 상품 커버율):\n")
w("| 공급사 | 상품수 | 커버율 |")
w("|---|---|---|")
for sup, cnt in top_suppliers.items():
    w(f"| {sup} | {cnt} | {cnt/total_unique:.1%} |")
w("")

w("### (7) 소분류별 경쟁 강도 (공급사 수 / 고유 상품 수)\n")
competition = df.groupby(["중분류", "소분류"]).agg(
    고유상품=("마스터코드", "nunique"),
    공급사수=("공급사", "nunique"),
)
competition["경쟁강도"] = competition["공급사수"] / competition["고유상품"]
competition = competition.sort_values("경쟁강도", ascending=False).head(15)
w("경쟁 강도 TOP 15 (공급사수/상품수 비율이 높을수록 경쟁 심함):\n")
w("| 중분류 | 소분류 | 상품 | 공급사 | 강도 |")
w("|---|---|---|---|---|")
for (mid, sub), row in competition.iterrows():
    w(f"| {mid} | {sub} | {int(row['고유상품'])} | {int(row['공급사수'])} | {row['경쟁강도']:.1f} |")

# 파일 저장
OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"마크다운 리포트 저장 완료: {OUTPUT_PATH}")
