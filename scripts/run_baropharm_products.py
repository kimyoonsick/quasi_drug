"""바로팜 상품 스크래퍼 실행 스크립트

사용법:
  uv run python scripts/run_baropharm_products.py              # 전체 실행
  uv run python scripts/run_baropharm_products.py --store-id 4207   # 특정 업체
  uv run python scripts/run_baropharm_products.py --max-stores 3    # 최대 3개
  uv run python scripts/run_baropharm_products.py --headless        # headless 모드
"""
import sys
import asyncio
import argparse
from pathlib import Path

# Windows cp949 인코딩 문제 방지
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers.baropharm_product import BaropharmProductScraper


def parse_args():
    parser = argparse.ArgumentParser(description="바로팜 상품 스크래퍼")
    parser.add_argument("--store-id", type=str, default=None,
                        help="특정 업체 ID만 스크래핑 (디버그용)")
    parser.add_argument("--max-stores", type=int, default=None,
                        help="최대 업체 수 제한")
    parser.add_argument("--csv", type=str, default=None,
                        help="업체 리스트 CSV 경로 (미지정 시 기본값)")
    parser.add_argument("--headless", action="store_true",
                        help="headless 모드 실행")
    return parser.parse_args()


async def main():
    args = parse_args()
    scraper = BaropharmProductScraper(
        headless=args.headless,
        max_stores=args.max_stores,
        target_store_id=args.store_id,
        store_csv=args.csv,
    )
    products = await scraper.run()
    print(f"\n최종 수집: {len(products)}개 상품")


if __name__ == "__main__":
    asyncio.run(main())
