# main.py
"""4개 약국 쇼핑몰 이벤트 통합 스크래퍼

대상: HMP몰, 바로팜, 새로팜, 플랫폼팜
각 사이트 실패 시 다른 사이트는 계속 진행
최종 결과를 competitor_raw.csv로 통합 저장
"""
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime

from scrapers.hmp_scraper import HmpEventScraper
from scrapers.baropharm_scraper import BaropharmEventScraper
from scrapers.saeropharm_scraper import SaeropharmEventScraper
from scrapers.platpharm_scraper import PlatpharmEventScraper
from process_csv import process_all_csvs

BASE_DIR = Path(__file__).resolve().parent


async def run_all(headless: bool = False):
    """모든 스크래퍼를 순차 실행"""
    scrapers = [
        HmpEventScraper(),
        SaeropharmEventScraper(),
        PlatpharmEventScraper(),
        BaropharmEventScraper(),  # 바로팜은 가장 신중하게 → 마지막
    ]

    all_events = []
    results_summary = []

    for scraper in scrapers:
        try:
            events = await scraper.run(headless=headless)
            all_events.extend(events)
            results_summary.append(f"  ✅ {scraper.name}: {len(events)}건")
        except Exception as e:
            results_summary.append(f"  ❌ {scraper.name}: 실패 ({e})")
            print(f"\n[{scraper.name}] 오류 발생, 다음 사이트로 진행: {e}")

    # 통합 CSV 저장
    print(f"\n{'='*50}")
    print("📊 수집 결과 요약")
    print(f"{'='*50}")
    for line in results_summary:
        print(line)

    if all_events:
        df = pd.DataFrame(all_events)
        timestamp = datetime.now().strftime('%y%m%d_%H%M')
        output_path = BASE_DIR / f"competitor_raw.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n📁 통합 저장: {output_path} (총 {len(df)}건)")

        # 타임스탬프 백업도 저장
        backup_path = BASE_DIR / "data" / f"competitor_raw_{timestamp}.csv"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(backup_path, index=False, encoding="utf-8-sig")
        print(f"📁 백업 저장: {backup_path}")
        
        # 추가: 스크래핑 완료 후 새로 지정한 10개 헤더 규격으로 가공 (processor)
        print(f"\n{'='*50}")
        print("🛠️ 통합 데이터 가공 시작 (10개 지정 헤더 맵핑)")
        print(f"{'='*50}")
        process_all_csvs()

    else:
        print("\n⚠️ 수집된 이벤트가 없습니다.")

    return all_events


def main():
    """동기 진입점"""
    asyncio.run(run_all(headless=False))


if __name__ == "__main__":
    main()
