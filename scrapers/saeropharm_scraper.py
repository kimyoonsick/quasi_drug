# scrapers/saeropharm_scraper.py
"""새로팜 (saeropharm.com) 이벤트 스크래퍼

로그인: id / pw 환경변수 (아이디 형식)
이벤트: /w/event/ingEvent.do 페이지
이벤트 상세: 각 이벤트 클릭하여 상세 페이지 방문

새로팜도 스크래핑 탐지에 유의해야 함.
"""
import os
import re
from .base import BaseEventScraper, BASE_DIR
from .bot_helper import human_delay, human_scroll, human_mouse_move


class SaeropharmEventScraper(BaseEventScraper):
    name = "saeropharm"
    delay_min = 8.0
    delay_max = 15.0

    LOGIN_URL = "https://www.saeropharm.com/front/login/login.do?"
    EVENT_URL = "https://www.saeropharm.com/w/event/ingEvent.do"
    BASE_URL = "https://www.saeropharm.com"

    def __init__(self):
        super().__init__()
        self.username = os.getenv("id")
        self.password = os.getenv("pw")

    async def login(self):
        """새로팜 아이디 로그인"""
        await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
        await human_delay(1, 3)
        await human_mouse_move(self.page)

        # 이미 로그인되어 메인으로 튕긴 경우 체크
        if "login" not in self.page.url and "Login" not in self.page.url:
            print("[saeropharm] 이미 세션 유지 중 (로그인 건너뜀)")
            return

        # 아이디 입력
        user_input = await self.page.query_selector('input[name="userId"]')
        if not user_input:
            user_input = await self.page.query_selector('input[name="memId"]')
        if not user_input:
            user_input = await self.page.query_selector('input[id="userId"]')

        if user_input:
            await user_input.click()
            await human_delay(0.2, 0.5)
            await user_input.fill(self.username)
            await human_delay(0.3, 0.8)

        # 비밀번호 입력
        pw_input = await self.page.query_selector('input[name="userPw"]')
        if not pw_input:
            pw_input = await self.page.query_selector('input[name="memPw"]')
        if not pw_input:
            pw_input = await self.page.query_selector('input[type="password"]')

        if pw_input:
            await pw_input.click()
            await human_delay(0.2, 0.5)
            await pw_input.fill(self.password)
            await human_delay(0.5, 1.0)

        # 로그인 버튼 클릭
        login_btn = await self.page.query_selector('a[href="javascript:loginChkEncrypt();"]')
        if not login_btn:
            login_btn = await self.page.query_selector('button:has-text("로그인")')
        if not login_btn:
            login_btn = await self.page.query_selector('a:has-text("로그인")')
        if not login_btn:
            login_btn = await self.page.query_selector('a:has-text("입장")')
        if not login_btn:
            login_btn = await self.page.query_selector('input[type="submit"]')

        if login_btn:
            await login_btn.click()
        else:
            await self.page.keyboard.press("Enter")

        await self.page.wait_for_load_state("networkidle")
        await human_delay(2, 4)

    async def extract_events(self) -> list[dict]:
        """새로팜 이벤트 목록 수집 - 클릭 기반 탐색

        1단계: 목록 페이지에서 이벤트 요소 파악
        2단계: 각 이벤트 클릭 → 상세 페이지 방문 → 이미지 다운로드
        """
        await self.page.goto(self.EVENT_URL, wait_until="domcontentloaded")
        await human_delay(2, 4)
        await human_scroll(self.page)

        # ── 1단계: 이벤트 목록 메타데이터 수집 (정확한 셀렉터) ──
        events_meta = await self.page.evaluate("""() => {
            const events = [];
            const baseUrl = 'https://www.saeropharm.com';

            // 정확한 이벤트 리스트 컨테이너 선택
            let items = Array.from(document.querySelectorAll('ul.article.ty-gallery > li > a.event-view, a.event-view'));

            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                const img = item.querySelector('div.thumb img');
                
                let title = '';
                const titleEl = item.querySelector('div.dscr strong');
                if (titleEl) {
                    title = titleEl.textContent.trim();
                } else if (img) {
                    title = img.alt || img.title || '';
                }

                let imgSrc = '';
                if (img) {
                    imgSrc = img.src || img.dataset.src || '';
                    if (imgSrc && !imgSrc.startsWith('http')) {
                        imgSrc = baseUrl + (imgSrc.startsWith('/') ? '' : '/') + imgSrc;
                    }
                }

                // data-idx 추출하여 상세 페이지 URL 구성
                let detailUrl = item.href || '';
                const idx = item.getAttribute('data-idx');
                if (idx) {
                    detailUrl = baseUrl + '/w/event/ingEventView.do?idx=' + idx;
                } else if (detailUrl.includes('javascript:')) {
                    const onclick = item.getAttribute('onclick') || detailUrl;
                    const match = onclick.match(/idx=(\\d+)/);
                    if (match) {
                        detailUrl = baseUrl + '/w/event/ingEventView.do?idx=' + match[1];
                    }
                }

                if (detailUrl && !detailUrl.startsWith('http')) {
                    detailUrl = baseUrl + (detailUrl.startsWith('/') ? '' : '/') + detailUrl;
                }

                // 날짜 추출
                let duration = '';
                const dateEl = item.querySelector('div.dscr span');
                if (dateEl) {
                    duration = dateEl.textContent.trim();
                }

                if (title || imgSrc) {
                    events.push({
                        index: i,
                        title: title,
                        img_src: imgSrc,
                        detail_url: detailUrl,
                        duration: duration,
                    });
                }
            }
            return events;
        }""")

        print(f"  [새로팜] 이벤트 {len(events_meta)}건 감지")

        # 디버깅: 발견된 이벤트 출력
        for m in events_meta:
            print(f"    - {m.get('title', '')[:50]} | {m.get('detail_url', '')[:80]}")

        results = []

        # ── 2단계: 각 이벤트 상세 페이지 방문 ──────────────────
        for idx, meta in enumerate(events_meta):
            event_title = meta.get("title", "").strip()
            thumb_url = meta.get("thumb_url", meta.get("img_src", ""))
            detail_url = meta.get("detail_url", "")

            print(f"  [{idx+1}/{len(events_meta)}] {event_title[:50]}")

            event = {
                "mall_name": "Saeropharm",
                "event_title": event_title,
                "duration": meta.get("duration", ""),
                "detail_url": detail_url,
                "thumbnail_url": thumb_url,
                "benefit_summary": "",
                "target": "",
                "detail_images": "",
            }

            # 썸네일 다운로드
            if thumb_url:
                await self.download_event_images(event, [thumb_url])

            # 상세 페이지 방문
            if detail_url and detail_url.startswith("http") and "javascript:" not in detail_url:
                try:
                    if idx > 0:
                        await self._delay(6, 12)
                    else:
                        await self._delay(3, 5)

                    await self.page.goto(detail_url, wait_until="domcontentloaded")
                    await human_delay(2, 4)
                    await human_scroll(self.page)

                    # 상세 페이지 이미지 수집
                    detail_images = await self.page.evaluate("""() => {
                        const baseUrl = 'https://www.saeropharm.com';
                        const imgs = Array.from(document.querySelectorAll('img'));
                        return imgs
                            .map(i => {
                                let src = i.src || '';
                                if (src && !src.startsWith('http')) src = baseUrl + src;
                                return src;
                            })
                            .filter(src =>
                                src &&
                                !src.includes('/icon') &&
                                !src.includes('/logo') &&
                                !src.includes('/btn_') &&
                                !src.includes('/bg_') &&
                                !src.includes('/common/') &&
                                !src.includes('ico_') &&
                                (src.includes('/upload') || src.includes('/event') || src.includes('/img/'))
                            );
                    }""")

                    if detail_images:
                        paths = await self.download_event_images(event, detail_images[:10])
                        event["detail_images"] = "|".join(paths)
                        print(f"    → 이미지 {len(paths)}장 다운로드")

                    # 혜택 정보 추출
                    benefit_text = await self.page.evaluate("""() => {
                        const el = document.querySelector('.event_view, .evt_detail, .board_view, .view_cont, #content');
                        return el ? el.textContent.trim().substring(0, 500) : '';
                    }""")
                    if benefit_text:
                        event["benefit_summary"] = benefit_text[:200]

                except Exception as e:
                    print(f"    → 상세 페이지 오류: {e}")

            results.append(event)

        # 목록 페이지로 복귀
        if results:
            await self.page.goto(self.EVENT_URL, wait_until="domcontentloaded")

        return results


if __name__ == "__main__":
    import asyncio
    scraper = SaeropharmEventScraper()
    data = asyncio.run(scraper.run())
    print(f"수집 완료: {len(data)}건")
