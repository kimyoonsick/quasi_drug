import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scrapers.saeropharm_scraper import SaeropharmEventScraper

async def check():
    s = SaeropharmEventScraper()
    await s.start_browser(headless=False)
    await s.login()
    await s.page.goto(s.EVENT_URL, wait_until="networkidle")
    
    from scrapers.bot_helper import human_delay, human_scroll
    await human_delay(2,3)
    await human_scroll(s.page)
    await human_delay(1,2)
    
    # img 태그 중에서 이벤트와 관련 있을 만한 요소 찾기
    imgs = await s.page.query_selector_all("a img")
    print(f"Total img inside a tags: {len(imgs)}")
    
    for img in imgs:
        src = await img.get_attribute("src")
        alt = await img.get_attribute("alt")
        
        # 상위 a 태그의 href
        a_tag = await img.evaluate_handle('el => el.closest("a")')
        if a_tag:
            href_val = await a_tag.evaluate('el => el.href')
            onclick_val = await a_tag.evaluate('el => el.getAttribute("onclick")')
            
            # 쓸데없는 로고나 아이콘은 제외하고 출력
            if src and "logo" not in src and "icon" not in src and "assets" not in src:
                print(f"Image Src: {src}")
                print(f"Alt: {alt}")
                print(f"Href: {href_val}")
                print(f"Onclick: {onclick_val}")
                print("-" * 40)
    
    await s.stop_browser()

asyncio.run(check())
