# scrapers/hmp_scraper.py
"""HMP몰 (hmpmall.co.kr) 이벤트 스크래퍼

로그인: id / pw 환경변수 (아이디 형식)
이벤트: /event/eventList.do 페이지에서 이미지 카드 형태로 제공
상세 페이지: javascript:eventMain.goEventDetail(ID,TYPE) 클릭으로 이동

전략:
1. 이벤트 목록 페이지에서 모든 이벤트 링크 수집
2. 각 이벤트를 직접 클릭하여 상세 페이지로 이동
3. 상세 페이지에서 이미지 다운로드
4. 뒤로가기로 목록 페이지 복귀
5. 다음 이벤트 클릭
"""
import os
import re
from .base import BaseEventScraper, BASE_DIR
from .bot_helper import human_delay, human_scroll, human_mouse_move, scroll_to_bottom


class HmpEventScraper(BaseEventScraper):
    name = "hmp"
    delay_min = 8.0
    delay_max = 15.0

    LOGIN_URL = "https://www.hmpmall.co.kr/login.do"
    EVENT_URL = "https://www.hmpmall.co.kr/event/eventList.do?pageDtlNum=MNMU0003"
    BASE_URL = "https://www.hmpmall.co.kr"

    def __init__(self):
        super().__init__()
        self.username = os.getenv("id")
        self.password = os.getenv("pw")

    async def login(self):
        await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
        await human_delay(1, 2)

        # 아이디 입력
        await self.page.fill('input[name="memId"]', self.username)
        await human_delay(0.3, 0.8)

        # 비밀번호 입력
        await self.page.fill('input[name="memPw"]', self.password)
        await human_delay(0.5, 1.0)

        # 로그인 버튼 클릭
        login_btn = await self.page.query_selector('a[href="javascript:login.login();"]')
        if login_btn:
            await login_btn.click()
        else:
            btn = await self.page.query_selector('button:has-text("로그인")')
            if btn:
                await btn.click()
            else:
                await self.page.keyboard.press("Enter")

        await self.page.wait_for_load_state("networkidle")
        await human_delay(2, 4)

    async def extract_events(self) -> list[dict]:
        """HMP몰 이벤트 목록 수집 - 클릭 기반 탐색"""
        await self.page.goto(self.EVENT_URL, wait_until="domcontentloaded")
        await human_delay(2, 4)

        # 페이지 끝까지 스크롤하여 모든 이벤트 로드
        await scroll_to_bottom(self.page)

        # ── 1단계: 이벤트 목록 메타데이터 수집 ────────────────
        events_meta = await self.page.evaluate("""() => {
            const events = [];
            // HMP몰 구조: <a href="javascript:eventMain.goEventDetail(ID,TYPE)">
            //               <img src="..." title="이벤트 제목">
            //             </a>
            const links = document.querySelectorAll('a[href*="goEventDetail"]');

            for (let i = 0; i < links.length; i++) {
                const a = links[i];
                const img = a.querySelector('img');

                // img.title에 이벤트 제목이 있음
                let title = '';
                if (img) title = img.title || img.alt || '';
                if (!title) title = a.textContent.trim().substring(0, 100);

                // href에서 이벤트 ID 추출
                let eventId = '';
                const match = a.href.match(/goEventDetail\\((\\d+)/);
                if (match) eventId = match[1];

                // 썸네일 URL
                let thumbUrl = '';
                if (img) {
                    thumbUrl = img.src || '';
                    if (thumbUrl.startsWith('//')) thumbUrl = 'https:' + thumbUrl;
                }

                events.push({
                    index: i,
                    title: title,
                    event_id: eventId,
                    thumb_url: thumbUrl,
                });
            }
            return events;
        }""")

        print(f"  [HMP] 이벤트 {len(events_meta)}건 감지")

        results = []

        # ── 2단계: 각 이벤트 클릭 → 상세 페이지 방문 ──────────
        for idx, meta in enumerate(events_meta):
            event_title = meta.get("title", "").strip()
            event_id = meta.get("event_id", "")
            thumb_url = meta.get("thumb_url", "")

            print(f"  [{idx+1}/{len(events_meta)}] {event_title or event_id}")

            event = {
                "mall_name": "HMP",
                "event_title": event_title,
                "event_id": event_id,
                "duration": "",
                "detail_url": "",
                "thumbnail_url": thumb_url,
                "benefit_summary": "",
                "target": "",
                "detail_images": "",
            }

            try:
                # 이벤트 목록 페이지로 이동 (매번 새로 로드하여 안정성 확보)
                if idx > 0:
                    await self._delay(5, 10)
                    await self.page.goto(self.EVENT_URL, wait_until="domcontentloaded")
                    await human_delay(2, 3)

                # 해당 이벤트의 링크를 찾아서 클릭
                event_links = await self.page.query_selector_all('a[href*="goEventDetail"]')
                if meta["index"] < len(event_links):
                    link = event_links[meta["index"]]

                    # 자연스럽게 스크롤하여 요소가 보이게 함
                    await link.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)

                    # 클릭
                    await link.click()
                    await self.page.wait_for_load_state("domcontentloaded")
                    await human_delay(2, 4)

                    # 현재 URL 저장
                    event["detail_url"] = self.page.url

                    # 자연스럽게 스크롤
                    await human_scroll(self.page)

                    # ── 상세 페이지에서 이미지 수집 ──────────
                    detail_images = await self.page.evaluate("""() => {
                        const imgs = Array.from(document.querySelectorAll('img'));
                        return imgs
                            .map(i => {
                                let src = i.src || '';
                                if (src.startsWith('//')) src = 'https:' + src;
                                return src;
                            })
                            .filter(src =>
                                src &&
                                !src.includes('/icon') &&
                                !src.includes('/logo') &&
                                !src.includes('/btn_') &&
                                !src.includes('/bg_') &&
                                !src.includes('/common/') &&
                                !src.includes('statics/imgs/bpco') &&
                                src.includes('/upload/')
                            );
                    }""")

                    if detail_images:
                        paths = await self.download_event_images(event, detail_images[:10])
                        event["detail_images"] = "|".join(paths)
                        print(f"    → 이미지 {len(paths)}장 다운로드")
                    else:
                        # 폴백: 모든 큰 이미지 수집
                        all_images = await self.page.evaluate("""() => {
                            const imgs = Array.from(document.querySelectorAll('img'));
                            return imgs
                                .filter(i => i.naturalWidth > 200 || i.width > 200)
                                .map(i => {
                                    let src = i.src || '';
                                    if (src.startsWith('//')) src = 'https:' + src;
                                    return src;
                                })
                                .filter(src => src && !src.includes('/common/'));
                        }""")
                        if all_images:
                            paths = await self.download_event_images(event, all_images[:5])
                            event["detail_images"] = "|".join(paths)
                            print(f"    → 이미지 {len(paths)}장 다운로드 (폴백)")

                    # 혜택/기간 정보 추출
                    page_text = await self.page.evaluate("""() => {
                        const el = document.querySelector('.sub_content, .content_area, #content');
                        return el ? el.textContent.trim().substring(0, 500) : '';
                    }""")
                    if page_text:
                        # 기간 패턴 찾기
                        date_match = re.search(
                            r'(\d{4}[./-]\d{1,2}[./-]\d{1,2})\s*[~-]\s*(\d{4}[./-]\d{1,2}[./-]\d{1,2})',
                            page_text
                        )
                        if date_match:
                            event["duration"] = f"{date_match.group(1)} ~ {date_match.group(2)}"

                else:
                    print(f"    → 링크를 찾을 수 없음, 스킵")

            except Exception as e:
                print(f"    → 오류: {e}")

            # 썸네일도 다운로드 (아직 없다면)
            if thumb_url and not event.get("detail_images"):
                await self.download_event_images(event, [thumb_url])

            results.append(event)

        return results


if __name__ == "__main__":
    import asyncio
    scraper = HmpEventScraper()
    data = asyncio.run(scraper.run())
    print(f"수집 완료: {len(data)}건")
