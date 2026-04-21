"""바로팜 + 플랫팜만 테스트 실행"""
import asyncio
from scrapers.baropharm_scraper import BaropharmEventScraper
from scrapers.platpharm_scraper import PlatpharmEventScraper
from process_csv import process_all_csvs

async def run_test():
    for Scraper in [BaropharmEventScraper, PlatpharmEventScraper]:
        scraper = Scraper()
        try:
            await scraper.run(headless=False)
        except Exception as e:
            print(f"[{scraper.name}] 오류: {e}")

    print("\n== CSV 가공 ==")
    process_all_csvs()

if __name__ == "__main__":
    asyncio.run(run_test())
