# scrapers/bot_helper.py
"""봇 탐지 회피를 위한 유틸리티 모듈

- stealth 브라우저 컨텍스트 설정
- 자연스러운 인간적 행동 시뮬레이션
- 캡차/봇 챌린지 탐지 및 처리
"""
import os
import random
import asyncio
from playwright.async_api import Page, BrowserContext, Browser


# ── 실제 Chrome User-Agent 로테이션 ──────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


async def create_stealth_context(browser: Browser, **kwargs):
    """봇 탐지 우회를 위한 특수 브라우저 컨텍스트 생성"""
    default_args = {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "ko-KR",
        "timezone_id": "Asia/Seoul",
        "color_scheme": "light",
        "screen": {"width": 1920, "height": 1080},
        "java_script_enabled": True,
    }
    
    # kwargs 우선 적용
    context_args = {**default_args, **kwargs}
    
    context = await browser.new_context(**context_args)

    # navigator.webdriver 숨기기 + 플러그인 위장
    await context.add_init_script("""
        // webdriver 속성 숨기기
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

        // 플러그인 위장 (빈 배열이면 봇으로 탐지됨)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // 언어 위장
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en']
        });

        // Chrome 런타임 위장
        window.chrome = {runtime: {}};
    """)

    return context


async def human_delay(min_sec: float = 2.0, max_sec: float = 5.0):
    """인간적인 랜덤 딜레이"""
    wait = random.uniform(min_sec, max_sec)
    await asyncio.sleep(wait)


async def human_scroll(page: Page, direction: str = "down", amount: int = 0):
    """자연스러운 스크롤 시뮬레이션"""
    if amount == 0:
        amount = random.randint(200, 600)
    steps = random.randint(3, 6)
    step_amount = amount // steps

    for _ in range(steps):
        delta = step_amount + random.randint(-30, 30)
        if direction == "down":
            await page.mouse.wheel(0, delta)
        else:
            await page.mouse.wheel(0, -delta)
        await asyncio.sleep(random.uniform(0.1, 0.3))


async def human_mouse_move(page: Page):
    """랜덤 마우스 이동 (인간적 행동)"""
    x = random.randint(100, 1200)
    y = random.randint(100, 600)
    await page.mouse.move(x, y, steps=random.randint(5, 15))
    await asyncio.sleep(random.uniform(0.2, 0.5))


async def human_click(page: Page, selector: str, timeout: int = 10000):
    """인간적인 클릭 (호버 → 짧은 대기 → 클릭)"""
    element = await page.wait_for_selector(selector, timeout=timeout)
    if element:
        box = await element.bounding_box()
        if box:
            # 요소 중앙에서 약간 벗어난 위치로 마우스 이동
            x = box["x"] + box["width"] / 2 + random.randint(-5, 5)
            y = box["y"] + box["height"] / 2 + random.randint(-3, 3)
            await page.mouse.move(x, y, steps=random.randint(5, 10))
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.mouse.click(x, y)
        else:
            await element.click()


async def handle_bot_challenge(page: Page):
    """봇 챌린지(캡차) 탐지 및 처리

    1. 숫자 입력 캡차 탐지
    2. BOT_CODE 환경변수로 자동 입력 시도
    3. 없으면 수동 입력 요청 (콘솔)
    """
    try:
        # 일반적인 캡차 셀렉터들 확인
        challenge_input = await page.query_selector('input[name="captcha"]')
        if not challenge_input:
            challenge_input = await page.query_selector('input[placeholder*="숫자"]')
        if not challenge_input:
            challenge_input = await page.query_selector('input[placeholder*="보안"]')
        if not challenge_input:
            return  # 챌린지 없음

        code = os.getenv("BOT_CODE")
        if not code:
            print("[Bot] 숫자 보안 챌린지 감지! 브라우저에 표시된 코드를 입력하세요:")
            code = input("코드 입력: ")

        await challenge_input.fill(code)
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()
        await page.wait_for_load_state("networkidle")
    except Exception as e:
        print(f"[Bot] 챌린지 처리 오류: {e}")


async def block_analytics_only(page: Page):
    """분석 스크립트만 선별적 차단 (이미지/폰트는 허용)

    이미지를 차단하면 오히려 봇 시그널이 될 수 있으므로,
    분석/추적 스크립트만 차단합니다.
    """
    await page.route("*clarity.ms*", lambda r: r.abort())
    await page.route("*microsoft.com/clarity*", lambda r: r.abort())
    await page.route("*googletagmanager.com*", lambda r: r.abort())
    await page.route("*google-analytics.com*", lambda r: r.abort())
    await page.route("*hotjar.com*", lambda r: r.abort())
    await page.route("*fullstory.com*", lambda r: r.abort())
    await page.route("*channel.io*", lambda r: r.abort())
