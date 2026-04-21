import asyncio
from scrapers.saeropharm_scraper import SaeropharmEventScraper

async def check():
    s = SaeropharmEventScraper()
    await s.start_browser(headless=False)
    await s.login()
    await s.page.goto(s.EVENT_URL, wait_until="domcontentloaded")
    
    # 3초 정도 기다린 후 스크롤도 한 번 수행
    from scrapers.bot_helper import human_delay, human_scroll
    await human_delay(2,3)
    await human_scroll(s.page)
    await human_delay(1,2)
    
    html = await s.page.content()
    with open("saeropharm_event_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("DOM 저장 완료")
    await s.stop_browser()

asyncio.run(check())
