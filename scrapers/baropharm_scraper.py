# scrapers/baropharm_scraper.py
"""바로팜 (baropharm.com) 이벤트 스크래퍼

⚠️ 바로팜은 상당한 IT 기업으로, 봇 탐지가 엄격합니다.
- 긴 딜레이 (10~20초)
- 리소스 차단 최소화
- 자연스러운 브라우징 패턴 유지

로그인: community.baropharm.com/signin (이메일 로그인)
환경변수: email_id, pw
이벤트: /events 페이지
"""
import os
from .base import BaseEventScraper, BASE_DIR
from .bot_helper import human_delay, human_scroll, human_mouse_move, scroll_to_bottom


class BaropharmEventScraper(BaseEventScraper):
    name = "baropharm"
    # 바로팜은 IT 기업이므로 딜레이를 더 길게
    delay_min = 10.0
    delay_max = 20.0

    LOGIN_URL = "https://community.baropharm.com/signin?from=https://www.baropharm.com/"
    EVENT_URL = "https://www.baropharm.com/events"
    BASE_URL = "https://www.baropharm.com"

    def __init__(self):
        super().__init__()
        self.username = os.getenv("baro_id") or os.getenv("email_id")
        self.password = os.getenv("baro_pw") or os.getenv("pw")

    async def login(self):
        """바로팜 이메일 로그인 (community.baropharm.com 서브도메인)"""
        # 먼저 메인 페이지에서 이미 로그인 되어있는지 확인
        await self.page.goto(self.BASE_URL, wait_until="domcontentloaded")
        await human_delay(2, 3)

        # 로그인 여부 체크: 페이지 텍스트에서 로그인 상태 판별
        is_logged_in = await self.page.evaluate("""() => {
            const body = document.body.innerText || '';
            if (body.includes('로그아웃') || body.includes('마이페이지')) return true;
            // 로그인/가입 링크가 보이면 미로그인
            const links = document.querySelectorAll('a');
            for (const a of links) {
                if (a.href && a.href.includes('signin')) return false;
                if (a.textContent && a.textContent.trim() === '로그인') return false;
            }
            return false;
        }""")

        if is_logged_in:
            print(f"  [Baropharm] 이미 세션 유지 중 (로그인 건너뜀)")
            return

        # 로그인 페이지로 이동
        await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
        await human_delay(2, 4)

        # 마우스 이동으로 인간적인 행동
        await human_mouse_move(self.page)

        # 로그인 폼이 존재하는지 확인 (비밀번호 필드로 판별)
        pw_input = await self.page.query_selector('input[type="password"]')
        if not pw_input:
            print(f"  [Baropharm] 로그인 폼 없음 (이미 로그인 상태로 추정)")
            return

        # 이메일 입력란 찾기 (여러 셀렉터 시도)
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="이메일"]',
            'input[placeholder*="아이디"]',
            'input[autocomplete="email"]',
        ]
        email_input = None
        for sel in email_selectors:
            email_input = await self.page.query_selector(sel)
            if email_input:
                break

        if not email_input:
            # 폴백: 첫 번째 텍스트/이메일 입력란
            inputs = await self.page.query_selector_all('input[type="text"], input[type="email"]')
            if inputs:
                email_input = inputs[0]

        if email_input:
            await email_input.click()
            await human_delay(0.2, 0.5)
            await email_input.fill(self.username)
            await human_delay(0.5, 1.0)

        # 비밀번호 입력
        if pw_input:
            await pw_input.click()
            await human_delay(0.2, 0.5)
            await pw_input.fill(self.password)
            await human_delay(0.5, 1.5)

        # 로그인 버튼 클릭
        login_selectors = [
            'button:has-text("로그인")',
            'button[type="submit"]',
            'a:has-text("로그인")',
            'input[type="submit"]',
        ]
        for sel in login_selectors:
            btn = await self.page.query_selector(sel)
            if btn:
                await human_delay(0.3, 0.8)
                await btn.click()
                break

        await self.page.wait_for_load_state("networkidle")
        await human_delay(3, 5)

    async def extract_events(self) -> list[dict]:
        """바로팜 이벤트 목록 수집

        ⚠️ 최대한 자연스럽게 탐색 - 급하게 데이터를 긁지 않음
        """
        # 자연스럽게 메인 페이지에서 잠시 머무른 후 이벤트 페이지로 이동
        print("  [Baropharm] 메인 페이지 탐색...")
        await human_scroll(self.page)
        await self._delay(2, 4)

        print(f"  [Baropharm] 이벤트 페이지 이동: {self.EVENT_URL}")
        await self.page.goto(self.EVENT_URL, wait_until="domcontentloaded")
        await human_delay(2, 4)

        # 페이지 끝까지 스크롤하여 모든 이벤트 로드
        await scroll_to_bottom(self.page)
        await human_delay(1, 2)

        results = []

        # 이벤트 데이터 추출
        events_data = await self.page.evaluate("""() => {
            const events = [];

            // 이벤트 카드/목록 아이템 찾기
            const selectors = [
                'a[href*="/events/"]',
                '[class*="event"] a',
                '.event-card', '.event-item',
                'article', '.card',
                '[class*="EventCard"]', '[class*="event-card"]',
            ];

            let items = [];
            for (const sel of selectors) {
                const found = document.querySelectorAll(sel);
                if (found.length > 0) {
                    items = found;
                    break;
                }
            }

            for (const item of items) {
                const img = item.querySelector('img');
                const link = item.closest('a') || item.querySelector('a');

                let title = '';
                // 제목 요소 찾기
                const titleEl = item.querySelector('h2, h3, h4, strong, .title, [class*="title"]');
                if (titleEl) title = titleEl.textContent.trim();
                if (!title && img) title = img.alt || '';
                if (!title) title = item.textContent.trim().substring(0, 100);

                let imgSrc = '';
                if (img) imgSrc = img.src || img.dataset.src || '';

                let detailUrl = '';
                if (link) detailUrl = link.href || '';

                let duration = '';
                const dateEl = item.querySelector('[class*="date"], [class*="period"], time, .duration');
                if (dateEl) duration = dateEl.textContent.trim();

                let benefit = '';
                const benefitEl = item.querySelector('[class*="benefit"], [class*="desc"], p');
                if (benefitEl) benefit = benefitEl.textContent.trim();

                if (title || imgSrc) {
                    events.push({
                        title, img_src: imgSrc, detail_url: detailUrl,
                        duration, benefit,
                        text: item.textContent.trim().substring(0, 200)
                    });
                }
            }
            return events;
        }""")
        
        print(f"  [Baropharm] 감지된 이벤트 수: {len(events_data)}")

        for ev in events_data:
            event = {
                "mall_name": "Baropharm",
                "event_title": ev.get("title", "").strip(),
                "duration": ev.get("duration", "").strip(),
                "benefit_summary": ev.get("benefit", "").strip(),
                "detail_url": ev.get("detail_url", ""),
                "thumbnail_url": ev.get("img_src", ""),
                "target": "",
            }
            results.append(event)

            if ev.get("img_src"):
                await self.download_event_images(event, [ev["img_src"]])

        # 상세 페이지 접근 - 모든 이벤트 방문
        for i, ev in enumerate(events_data):
            detail_url = ev.get("detail_url", "")
            if detail_url and detail_url.startswith("http"):
                try:
                    await self._delay(5, 10)
                    await human_mouse_move(self.page)
                    print(f"  [{i+1}/{len(events_data)}] 상세 방문: {results[i]['event_title'][:30]}")
                    await self.page.goto(detail_url, wait_until="domcontentloaded")
                    await human_delay(2, 4)

                    # 상세 페이지 끝까지 스크롤
                    await scroll_to_bottom(self.page, max_scrolls=10, wait_sec=1.0)

                    # 상세 페이지 이미지 수집 (넓은 필터)
                    detail_images = await self.page.evaluate("""() => {
                        const imgs = Array.from(document.querySelectorAll('img'));
                        return imgs.map(i => i.src)
                            .filter(src => src &&
                                !src.includes('icon') && !src.includes('logo') &&
                                !src.includes('avatar') && !src.includes('favicon') &&
                                !src.includes('/common/') && !src.includes('btn_') &&
                                !src.includes('loading') && !src.includes('placeholder') &&
                                (src.includes('http') && (
                                    src.includes('event') || src.includes('upload') ||
                                    src.includes('static') || src.includes('promotion') ||
                                    src.includes('banner') || src.includes('content') ||
                                    src.includes('img') || src.includes('image')
                                ))
                            );
                    }""")

                    if detail_images:
                        paths = await self.download_event_images(results[i], detail_images[:5])
                        results[i]["detail_images"] = "|".join(paths)
                        print(f"    → 이미지 {len(paths)}장 다운로드")
                    else:
                        print(f"    → 상세 이미지 없음")

                except Exception as e:
                    print(f"  [Baropharm] 상세 페이지 스킵: {e}")

        return results


if __name__ == "__main__":
    import asyncio
    scraper = BaropharmEventScraper()
    data = asyncio.run(scraper.run())
    print(f"수집 완료: {len(data)}건")
