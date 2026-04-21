import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scrapers.saeropharm_scraper import SaeropharmEventScraper

DEBUG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'debug')

async def check():
    s = SaeropharmEventScraper()
    await s.start_browser(headless=True)
    
    print("페이지 이동...")
    await s.page.goto(s.LOGIN_URL, wait_until="domcontentloaded")
    await s.page.screenshot(path=os.path.join(DEBUG_DIR, "saeropharm_login_1_init.png"), full_page=True)
    
    from scrapers.bot_helper import human_delay, human_mouse_move
    await human_delay(1, 2)
    
    # 아이디 입력
    user_input = await s.page.query_selector('input[id="userId"]')
    if user_input:
        await user_input.click()
        await user_input.fill(s.username)
        await human_delay(0.5, 1.0)
    
    # 패스워드 입력
    pw_input = await s.page.query_selector('input[id="userPw"]')
    if pw_input:
        await pw_input.click()
        await pw_input.fill(s.password)
        await human_delay(0.5, 1.0)
        
    await s.page.screenshot(path=os.path.join(DEBUG_DIR, "saeropharm_login_2_filled.png"), full_page=True)
    
    # 버튼 찾기 및 클릭
    login_btn = await s.page.query_selector('a:has-text("입장")')
    if login_btn:
        print("입장 버튼 클릭")
        await login_btn.click()
    else:
        print("버튼 없음. 엔터 입력")
        await s.page.keyboard.press("Enter")
        
    await s.page.wait_for_load_state("networkidle")
    await human_delay(2, 4)
    
    await s.page.screenshot(path=os.path.join(DEBUG_DIR, "saeropharm_login_3_result.png"), full_page=True)
    
    print("현재 URL:", s.page.url)
    
    await s.stop_browser()

asyncio.run(check())
