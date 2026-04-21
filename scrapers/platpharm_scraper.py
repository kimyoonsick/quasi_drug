# scrapers/platpharm_scraper.py
"""플랫폼팜 (platpharm.co.kr) 이벤트 스크래퍼

로그인: 홈페이지 로그인 폼 (이메일 로그인)
환경변수: email_id (또는 platpharm_id), pw (또는 platpharm_pw)
이벤트: /pharmacy/events 페이지
이벤트 상세: /pharmacy/events?eventId={ID}
"""
import os
from .base import BaseEventScraper, BASE_DIR
from .bot_helper import human_delay, human_scroll, human_mouse_move, scroll_to_bottom


class PlatpharmEventScraper(BaseEventScraper):
    name = "platpharm"
    delay_min = 8.0
    delay_max = 12.0

    LOGIN_URL = "https://www.platpharm.co.kr/"
    EVENT_URL = "https://www.platpharm.co.kr/pharmacy/events"
    BASE_URL = "https://www.platpharm.co.kr"

    def __init__(self):
        super().__init__()
        # platpharm_id가 있으면 사용, 없으면 email_id 폴백
        self.username = os.getenv("platpharm_id") or os.getenv("email_id")
        self.password = os.getenv("platpharm_pw") or os.getenv("pw")

    async def login(self):
        """플랫폼팜 이메일 로그인 (홈페이지 로그인 폼)"""
        # 먼저 메인 페이지에서 이미 로그인 되어있는지 확인
        await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
        await human_delay(2, 3)

        # 팝업 닫기 시도
        try:
            popup_close = await self.page.query_selector_all('button.close, [class*="modal"] button, [class*="close"]')
            if popup_close:
                for btn in popup_close:
                    if await btn.is_visible():
                        await btn.click(force=True)
                        await human_delay(0.5, 1)
        except Exception:
            pass

        # 로그인 여부 체크: 비밀번호 필드가 있으면 로그인 폼이 보이는 상태 = 미로그인
        pw_input = await self.page.query_selector('input[type="password"]')
        if not pw_input:
            # 비밀번호 필드 없음 → 로그인 되어있거나 이미 다른 페이지
            # 추가 확인: 마이플랫팜, 장바구니 등 로그인 후 메뉴가 보이는지
            is_logged_in = await self.page.evaluate("""() => {
                const body = document.body.innerText || '';
                if (body.includes('마이플랫팜') || body.includes('장바구니') || body.includes('로그아웃')) return true;
                // auth/login 페이지로 리다이렉트 되었는지 확인
                if (window.location.pathname.includes('/auth/login')) return false;
                return true;
            }""")
            if is_logged_in:
                print(f"  [Platpharm] 이미 세션 유지 중 (로그인 건너뜀)")
                return

        # 이메일 입력란 찾기
        email_selectors = [
            'input[placeholder="아이디(이메일)"]',
            'input[placeholder*="아이디"]',
            'input[placeholder*="이메일"]',
            'input[type="email"]',
            'input[name="email"]',
            'input[autocomplete="email"]',
        ]
        email_input = None
        for sel in email_selectors:
            email_input = await self.page.query_selector(sel)
            if email_input:
                break

        if not email_input:
            inputs = await self.page.query_selector_all('input[type="text"], input[type="email"]')
            if inputs:
                email_input = inputs[0]

        if email_input:
            await email_input.click(force=True)
            await human_delay(0.2, 0.5)
            await email_input.fill(self.username)
            await human_delay(0.5, 1.0)

        # 비밀번호 입력
        if pw_input:
            await pw_input.click(force=True)
            await human_delay(0.2, 0.5)
            await pw_input.fill(self.password)
            await human_delay(0.5, 1.5)

        # 로그인 버튼 클릭
        login_selectors = [
            'button.bg-emerald-3',
            'button.bg-primary',
            'button[type="submit"]',
            'button:has-text("로그인")',
        ]
        for sel in login_selectors:
            btn = await self.page.query_selector(sel)
            if btn:
                await human_delay(0.3, 0.8)
                await btn.click(force=True)
                break

        await self.page.wait_for_load_state("networkidle")
        await human_delay(3, 5)

        # 로그인 후 뜨는 팝업 닫기
        try:
            popup_close = await self.page.query_selector_all('button.close, [class*="modal"] button')
            if popup_close:
                for btn in popup_close:
                    if await btn.is_visible():
                        await btn.click(force=True)
                        await human_delay(0.5, 1)
        except Exception:
            pass

    async def extract_events(self) -> list[dict]:
        """플랫폼팜 이벤트 목록 수집

        플랫폼팜은 SPA(Next.js 등)로 되어 있을 수 있음.
        이벤트 카드 클릭 시 eventId 파라미터로 상세 이동.
        """
        await self.page.goto(self.EVENT_URL, wait_until="domcontentloaded")
        await human_delay(3, 5)

        # 페이지 끝까지 스크롤하여 모든 이벤트 로드
        await scroll_to_bottom(self.page)
        await human_delay(1, 2)

        results = []

        # 이벤트 데이터 추출
        events_data = await self.page.evaluate("""() => {
            const events = [];
            const baseUrl = 'https://www.platpharm.co.kr';

            // 이벤트 카드 탐색
            const titleButtons = Array.from(document.querySelectorAll('button.title-18-medium'));
            
            for (let i = 0; i < titleButtons.length; i++) {
                const titleBtn = titleButtons[i];
                const cardContainer = titleBtn.closest('div.grid > div') || titleBtn.parentElement.parentElement;
                
                let title = titleBtn.innerText || titleBtn.textContent;
                title = title.trim();

                let imgSrc = '';
                const img = cardContainer ? cardContainer.querySelector('button.relative img') || cardContainer.querySelector('img') : null;
                if (img) {
                    imgSrc = img.src || img.dataset.src || '';
                    if (imgSrc && !imgSrc.startsWith('http')) {
                        imgSrc = baseUrl + imgSrc;
                    }
                }

                // 기간 추출: 제목 주변의 내용에서 날짜 포맷 찾기
                let duration = '';
                if (cardContainer) {
                    const text = cardContainer.textContent || '';
                    const dateMatch = text.match(/(\\d{4}[\\./\\- ]\\d{1,2}[\\./\\- ]\\d{1,2})\\s*[~\\-]\\s*(\\d{4}[\\./\\- ]\\d{1,2}[\\./\\- ]\\d{1,2}|\\d+[\\./\\- ]\\d{1,2}[\\./\\- ]\\d{1,2})/);
                    if (dateMatch) duration = dateMatch[0].trim();
                }

                // category나 badge 찾기
                let category = '';
                if (cardContainer) {
                    const badge = cardContainer.querySelector('[class*="badge"], [class*="tag"]');
                    if (badge) category = badge.textContent.trim();
                }

                // ID 또는 URL 추출
                // 버튼을 구조상으로 클릭하게 하려면 직접 URL을 만들거나 나중에 python에서 index를 통해 클릭해야 함.
                // 일단 이벤트 index를 반환
                if (title && title.length > 2) {
                    events.push({
                        index: i,
                        title: title,
                        img_src: imgSrc,
                        duration: duration,
                        category: category
                    });
                }
            }
            return events;
        }""")

        for ev in events_data:
            event = {
                "mall_name": "Platpharm",
                "event_title": ev.get("title", "").strip(),
                "duration": ev.get("duration", "").strip(),
                "detail_url": ev.get("detail_url", ""),
                "thumbnail_url": ev.get("img_src", ""),
                "benefit_summary": ev.get("category", "").strip(),
                "target": "",
                "detail_images": ""
            }
            results.append(event)

            if ev.get("img_src"):
                await self.download_event_images(event, [ev["img_src"]])

        print(f"  [Platpharm] 발견된 이벤트 수: {len(results)}")

        # ── 2단계: 클릭으로 이벤트 상세 진입 ──
        # 주의: 봇 탐지와 시간 제약을 위해 최대 5개 정도만 방문
        for i in range(min(5, len(results))):
            try:
                # 이벤트 페이지가 상태 초기화 될 수 있으므로, 다시 쿼리
                title_buttons = await self.page.query_selector_all('button.title-18-medium')
                if i < len(title_buttons):
                    btn = title_buttons[i]
                    print(f"  [Platpharm] 상세 페이지 방문: {results[i]['event_title'][:30]}")
                    
                    # 스크롤해서 보이기
                    await btn.scroll_into_view_if_needed()
                    await human_delay(1, 2)
                    await btn.click()
                    await human_delay(2, 4)
                    
                    # 상세 URL 업데이트
                    results[i]["detail_url"] = self.page.url
                    
                    # 상세 페이지 이미지 수집 (SPA이므로 DOM이 변경됨)
                    detail_images = await self.page.evaluate("""() => {
                        const imgs = Array.from(document.querySelectorAll('main img, div[class*="Detail"] img, div[class*="event-content"] img'));
                        return imgs.map(img => img.src)
                            .filter(src => src && 
                                          !src.includes('icon') && 
                                          !src.includes('logo') && 
                                          !src.includes('avatar') &&
                                          !src.includes('btn_'));
                    }""")
                    
                    if detail_images:
                        paths = await self.download_event_images(results[i], detail_images[:5])
                        results[i]["detail_images"] = "|".join(paths)
                        print(f"    → 이미지 {len(paths)}장 다운로드")

            except Exception as e:
                print(f"  [Platpharm] 상세 페이지 방문 중 오류: {e}")
                
            finally:
                # 다시 이벤트 메인 페이지로 복귀 (SPA 상태로 인한 타임아웃 방지)
                if "events?eventId" in self.page.url or "events/" in self.page.url:
                    try:
                        await self.page.go_back(wait_until="domcontentloaded")
                    except Exception:
                        await self.page.goto(self.EVENT_URL, wait_until="domcontentloaded")
                    await human_delay(3, 5)

        return results


if __name__ == "__main__":
    import asyncio
    scraper = PlatpharmEventScraper()
    data = asyncio.run(scraper.run())
    print(f"수집 완료: {len(data)}건")
