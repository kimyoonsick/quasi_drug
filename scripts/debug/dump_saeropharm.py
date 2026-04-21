import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scrapers.saeropharm_scraper import SaeropharmEventScraper

async def run():
    s = SaeropharmEventScraper()
    await s.start_browser(headless=True)
    await s.login()
    await s.page.goto(s.EVENT_URL, wait_until='networkidle')
    await asyncio.sleep(3)
    html = await s.page.content()
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'debug', 'saeropharm_ingEvent.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    await s.stop_browser()
    print("Done")

if __name__ == "__main__":
    asyncio.run(run())
