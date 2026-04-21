import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scrapers.saeropharm_scraper import SaeropharmEventScraper

async def run_interactive():
    print("브라우저를 엽니다. 직접 로그인을 진행하고, 면허번호 등 추가 인증 창이 뜨면 닫아주세요.")
    print("완료하시면 브라우저를 직접 끄지 말고 이 콘솔 창에 엔터(Enter)를 눌러주세요.")
    s = SaeropharmEventScraper()
    await s.start_browser(headless=False)
    
    await s.page.goto(s.LOGIN_URL)
    
    # 아이디/비밀번호 자동 입력 시도
    try:
        user_input = await s.page.query_selector('input[id="userId"]')
        if user_input:
            await user_input.fill(s.username)
        pw_input = await s.page.query_selector('input[id="userPw"]')
        if pw_input:
            await pw_input.fill(s.password)
    except:
        pass
        
    await asyncio.get_event_loop().run_in_executor(None, input, "로그인 및 추가 인증 처리가 끝났다면 Enter를 누르세요...")
    
    print("상태를 저장하고 종료합니다.")
    await s.stop_browser()

if __name__ == "__main__":
    asyncio.run(run_interactive())
