# scrapers/baropharm_product.py
"""바로팜 (baropharm.com) 상품 스크래퍼

wholesalers 페이지에서 두 섹션의 업체 목록을 수집한 뒤,
각 업체 전용관(quasi-drug-mall/{ID})에 진입하여
카테고리별 상품(상품명, 규격, 가격)을 스크래핑한다.

섹션A: 바로팜 스토어 (카테고리 탭 + 스토어 전체보기)
섹션B: 의약외품   (이름순 정렬 + 카테고리 탭)

로그인: community.baropharm.com/signin
환경변수: baro_id, baro_pw
"""
import os
import re
import asyncio
import random
import csv
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from .bot_helper import (
    create_stealth_context,
    human_delay,
    human_scroll,
    human_mouse_move,
    scroll_to_bottom,
    block_analytics_only,
    handle_bot_challenge,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

WHOLESALERS_URL = "https://www.baropharm.com/wholesalers#wholesalers"
LOGIN_URL = "https://community.baropharm.com/signin?from=https://www.baropharm.com/"
STORE_URL_TMPL = "https://www.baropharm.com/quasi-drug-mall/{store_id}"

# 대상 카테고리 — 여기에만 추가하면 자동 반영
STORE_SECTION_CATEGORIES = ["의약외상품", "건강식품", "약국용품", "동물의약용품", "화장품"]
PRODUCT_SECTION_CATEGORIES = ["의약외상품", "건강식품", "약국용품", "동물의약용품", "화장품"]


class BaropharmProductScraper:
    name = "baropharm_product"
    delay_min = 15.0
    delay_max = 30.0

    def __init__(self, headless: bool = False, max_stores: int | None = None,
                 target_store_id: str | None = None):
        self.headless = headless
        self.max_stores = max_stores
        self.target_store_id = target_store_id
        self.username = os.getenv("baro_id") or os.getenv("email_id")
        self.password = os.getenv("baro_pw") or os.getenv("pw")
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None
        self.all_products: list[dict] = []

    # ── 브라우저 ──────────────────────────────────────────────

    async def start_browser(self):
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=self.headless)
        context_args = {
            "viewport": {"width": 1920, "height": 1080},
            "locale": "ko-KR",
            "timezone_id": "Asia/Seoul",
        }
        state_path = BASE_DIR / ".cookies" / f"{self.name}_state.json"
        if state_path.exists():
            context_args["storage_state"] = str(state_path)
        self.context = await create_stealth_context(self.browser, **context_args)
        self.page = await self.context.new_page()
        await block_analytics_only(self.page)

    async def stop_browser(self):
        if self.context:
            try:
                state_path = BASE_DIR / ".cookies" / f"{self.name}_state.json"
                state_path.parent.mkdir(parents=True, exist_ok=True)
                await self.context.storage_state(path=str(state_path))
            except Exception as e:
                print(f"[product] 세션 저장 오류: {e}")
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()

    async def _delay(self, min_sec: float | None = None, max_sec: float | None = None):
        _min = min_sec or self.delay_min
        _max = max_sec or self.delay_max
        if random.random() < 0.3:
            await human_mouse_move(self.page)
        if random.random() < 0.2:
            await human_scroll(self.page)
        await human_delay(_min, _max)

    # ── 로그인 ────────────────────────────────────────────────

    async def login(self):
        await self.page.goto("https://www.baropharm.com", wait_until="domcontentloaded")
        await human_delay(2, 3)

        is_logged_in = await self.page.evaluate("""() => {
            const body = document.body.innerText || '';
            if (body.includes('로그아웃') || body.includes('마이페이지')) return true;
            const links = document.querySelectorAll('a');
            for (const a of links) {
                if (a.href && a.href.includes('signin')) return false;
                if (a.textContent && a.textContent.trim() === '로그인') return false;
            }
            return false;
        }""")

        if is_logged_in:
            print("  [product] 이미 세션 유지 중 (로그인 건너뜀)")
            return

        await self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await human_delay(2, 4)
        await human_mouse_move(self.page)

        pw_input = await self.page.query_selector('input[type="password"]')
        if not pw_input:
            print("  [product] 로그인 폼 없음 (이미 로그인 상태로 추정)")
            return

        email_selectors = [
            'input[type="email"]', 'input[name="email"]',
            'input[placeholder*="이메일"]', 'input[placeholder*="아이디"]',
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
            await email_input.click()
            await human_delay(0.2, 0.5)
            await email_input.fill(self.username)
            await human_delay(0.5, 1.0)

        if pw_input:
            await pw_input.click()
            await human_delay(0.2, 0.5)
            await pw_input.fill(self.password)
            await human_delay(0.5, 1.5)

        for sel in ['button:has-text("로그인")', 'button[type="submit"]',
                    'a:has-text("로그인")', 'input[type="submit"]']:
            btn = await self.page.query_selector(sel)
            if btn:
                await human_delay(0.3, 0.8)
                await btn.click()
                break

        await self.page.wait_for_load_state("networkidle")
        await human_delay(3, 5)
        print("  [product] 로그인 완료")

    # ── Phase 1: 업체 목록 수집 (두 섹션 모두) ─────────────────

    async def collect_all_stores(self) -> list[dict]:
        """wholesalers 페이지에서 두 섹션의 업체를 수집
        
        SvelteKit SPA이므로 업체 엔트리는 <a> 태그가 아님.
        1) 팝업 닫기
        2) 각 섹션까지 스크롤 → lazy load 트리거
        3) pushState 인터셉트로 업체 클릭 시 URL 캡처
        """
        all_stores: dict[str, dict] = {}

        await self.page.goto(WHOLESALERS_URL, wait_until="networkidle")
        await human_delay(3, 5)
        await handle_bot_challenge(self.page)

        # 로그인 체크
        url_now = self.page.url
        print(f"  [Phase1] 현재 URL: {url_now}")
        if "signin" in url_now or "login" in url_now:
            print("  [Phase1] 재로그인")
            await self.login()
            await self.page.goto(WHOLESALERS_URL, wait_until="networkidle")
            await human_delay(3, 5)

        # 팝업/오버레이를 DOM에서 완전 제거 (스크롤 차단 해제)
        await self.page.evaluate("""() => {
            // 모달/팝업/오버레이 제거
            document.querySelectorAll('[class*="modal"], [class*="Modal"], [class*="popup"], [class*="Popup"], [class*="overlay"], [class*="Overlay"], [class*="dialog"], [class*="Dialog"]')
                .forEach(el => el.remove());
            // "오늘 하루 보지 않기" 텍스트를 가진 요소의 최상위 팝업 컨테이너 제거
            const all = Array.from(document.querySelectorAll('*'));
            for (const el of all) {
                if (el.textContent.trim() === '오늘 하루 보지 않기') {
                    // 3단계 위 부모까지 올라가서 제거 (팝업 컨테이너)
                    let target = el;
                    for (let i = 0; i < 5; i++) {
                        if (target.parentElement && target.parentElement !== document.body) {
                            target = target.parentElement;
                        }
                    }
                    target.remove();
                    break;
                }
            }
            // body overflow 강제 해제
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        }""")
        await human_delay(1, 2)

        # JavaScript로 전체 페이지 스크롤 (lazy load 트리거)
        print("  [Phase1] lazy load 트리거 스크롤")
        total_height = await self.page.evaluate("document.body.scrollHeight")
        for step in range(0, total_height + 2000, 500):
            await self.page.evaluate(f"window.scrollTo(0, {step})")
            await asyncio.sleep(0.5)
        await human_delay(2, 3)

        # 콘텐츠 로드 확인 (body 길이가 충분히 커질 때까지 대기)
        for attempt in range(10):
            body_len = await self.page.evaluate("document.body.innerText.length")
            if body_len > 5000:
                break
            # 추가 스크롤 시도
            new_height = await self.page.evaluate("document.body.scrollHeight")
            await self.page.evaluate(f"window.scrollTo(0, {new_height})")
            await asyncio.sleep(1)
        print(f"  [Phase1] body 길이: {body_len}")

        # 맨 위로 복귀
        await self.page.evaluate("window.scrollTo(0, 0)")
        await human_delay(1, 2)

        # ── Phase 1A: 바로팜 스토어 ──
        print("\n[Phase 1A] 바로팜 스토어 섹션")
        await self._scroll_to_section("바로팜 스토어")
        await human_delay(2, 3)

        for cat in STORE_SECTION_CATEGORIES:
            try:
                print(f"  [1A] {cat}")
                clicked = await self._click_section_tab(cat, section_index=0)
                if not clicked:
                    continue
                await human_delay(2, 3)
                new = await self._extract_store_entries("바로팜스토어", cat)
                self._merge_into(all_stores, new, "바로팜스토어", cat)
                print(f"    → {len(new)}개 업체")
                await human_delay(2, 4)
            except Exception as e:
                print(f"  [1A] {cat} 오류: {e}")

        # ── Phase 1B: 의약외품 ──
        print("\n[Phase 1B] 의약외품 섹션")
        await self._scroll_to_section("의약외품")
        await human_delay(2, 3)

        # 이름순 정렬
        sorted_ok = await self._click_name_sort_near("의약외품")
        print(f"  [1B] 이름순: {'적용' if sorted_ok else '없음'}")
        await human_delay(2, 3)

        for cat in PRODUCT_SECTION_CATEGORIES:
            try:
                print(f"  [1B] {cat}")
                clicked = await self._click_section_tab(cat, section_index=1)
                if not clicked:
                    continue
                await human_delay(2, 3)
                new = await self._extract_store_entries("의약외품", cat)
                self._merge_into(all_stores, new, "의약외품", cat)
                print(f"    → {len(new)}개 업체")
                await human_delay(2, 4)
            except Exception as e:
                print(f"  [1B] {cat} 오류: {e}")

        return sorted(all_stores.values(), key=lambda x: x["업체명"])

    async def _scroll_to_section(self, heading_text: str):
        await self.page.evaluate(f"""() => {{
            const els = Array.from(document.querySelectorAll('h1,h2,h3,h4,p,strong'));
            const el = els.find(e => e.textContent.trim() === '{heading_text}');
            if (el) el.scrollIntoView({{behavior:'smooth', block:'center'}});
        }}""")
        await human_delay(2, 3)

    async def _click_section_tab(self, cat_name: str, section_index: int = 0) -> bool:
        result = await self.page.evaluate(f"""() => {{
            const cands = Array.from(document.querySelectorAll('button,div,span,a'))
                .filter(el => el.textContent.trim() === '{cat_name}'
                    && el.children.length <= 1 && el.offsetParent !== null);
            const idx = Math.min({section_index}, cands.length - 1);
            if (idx >= 0 && cands[idx]) {{ cands[idx].click(); return {{ok:true, n:cands.length, i:idx}}; }}
            return {{ok:false, n:0, i:-1}};
        }}""")
        if result["ok"]:
            print(f"    탭 클릭 ({result['n']}개 중 #{result['i']})")
        else:
            print(f"    탭 '{cat_name}' 없음")
        return result["ok"]

    async def _click_name_sort_near(self, heading: str) -> bool:
        return await self.page.evaluate(f"""() => {{
            const all = Array.from(document.querySelectorAll('*'));
            const sec = all.find(e => e.textContent.trim() === '{heading}' && e.children.length <= 1);
            if (!sec) return false;
            const idx = all.indexOf(sec);
            for (let i = idx; i < Math.min(idx+50, all.length); i++) {{
                if (all[i].textContent.trim() === '이름순' && all[i].children.length <= 1) {{
                    all[i].click(); return true;
                }}
            }}
            return false;
        }}""")

    async def _extract_store_entries(self, section: str, cat: str) -> list[dict]:
        """업체 엔트리 추출 — SvelteKit SPA용
        
        <a> 태그가 없으므로 pushState를 인터셉트하여
        각 업체 클릭 시 이동할 URL을 캡처한다.
        """
        # 1차: <a> 태그 방식 (혹시 있으면)
        a_results = await self.page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .filter(a => /quasi-drug-mall|mall\\/\\d/.test(a.href))
                .map(a => {
                    const m = a.href.match(/(\\d+)\\/?$/);
                    return m ? {id: m[1], name: a.textContent.trim().split('\\n')[0].replace(/[>›»]+/g,'').trim(), href: a.href} : null;
                }).filter(Boolean);
        }""")
        if a_results:
            return [{"store_id": r["id"], "업체명": r["name"],
                     "url": r["href"], "출처섹션": [section], "도매카테고리": [cat]}
                    for r in a_results]

        # 2차: pushState 인터셉트 방식
        # 업체 엔트리 = ">" 텍스트를 포함하는 클릭 가능 요소
        store_data = await self.page.evaluate("""async () => {
            const results = [];
            
            // ">"를 포함하는 업체 엔트리 요소 수집
            const entries = Array.from(document.querySelectorAll('*')).filter(el => {
                if (el.offsetParent === null) return false;
                if (el.children.length > 5) return false;
                const t = el.textContent.trim();
                // "업체명 >" 패턴이고 적절한 길이
                if (!t.includes('>') && !t.includes('›')) return false;
                if (t.length < 2 || t.length > 80) return false;
                // 카테고리 탭이나 메뉴는 제외
                const skip = ['추천순','이름순','전체','통합주문','커뮤니티','브랜드관','멤버십','마이페이지'];
                if (skip.some(s => t.startsWith(s))) return false;
                // 부모 없거나 너무 큰 요소 제외
                const rect = el.getBoundingClientRect();
                if (rect.width < 50 || rect.height < 15) return false;
                return true;
            });
            
            // 각 업체를 클릭하고 pushState URL 캡처
            const origPush = history.pushState.bind(history);
            const origReplace = history.replaceState.bind(history);
            let captured = null;
            
            history.pushState = function(s, t, url) { captured = url; };
            history.replaceState = function(s, t, url) { captured = url; };
            
            const seen = new Set();
            for (const entry of entries) {
                captured = null;
                const name = entry.textContent.trim().split('\\n')[0]
                    .replace(/[>›»]/g, '').replace(/쿠폰|안심반품.*|적립.*|넘버|인기/g, '').trim();
                if (!name || name.length < 1 || seen.has(name)) continue;
                
                entry.click();
                // 짧은 대기 (마이크로태스크 실행)
                await new Promise(r => setTimeout(r, 100));
                
                if (captured) {
                    const m = String(captured).match(/(\\d+)\\/?$/);
                    if (m && !seen.has(m[1])) {
                        seen.add(m[1]);
                        seen.add(name);
                        results.push({id: m[1], name: name, url: String(captured)});
                    }
                }
            }
            
            // 원래 함수 복원
            history.pushState = origPush;
            history.replaceState = origReplace;
            
            return results;
        }""")

        if store_data:
            # pushState가 실제로 실행되었을 수 있으므로 wholesalers로 복귀
            current_url = self.page.url
            if "wholesalers" not in current_url:
                await self.page.goto(WHOLESALERS_URL, wait_until="domcontentloaded")
                await human_delay(3, 5)

            return [{"store_id": r["id"], "업체명": r["name"],
                     "url": f"https://www.baropharm.com/quasi-drug-mall/{r['id']}",
                     "출처섹션": [section], "도매카테고리": [cat]}
                    for r in store_data]

        # 디버그
        debug = await self.page.evaluate("""() => ({
            bodyLen: document.body.innerText.length,
            url: location.href,
            sample: document.body.innerText.substring(0, 500)
        })""")
        print(f"    [DEBUG] 추출 0개: {debug}")
        return []

    def _merge_into(self, all_stores: dict, new_stores: list, section: str, cat: str):
        for s in new_stores:
            sid = s["store_id"]
            if sid not in all_stores:
                all_stores[sid] = s
            else:
                if cat not in all_stores[sid]["도매카테고리"]:
                    all_stores[sid]["도매카테고리"].append(cat)
                if section not in all_stores[sid]["출처섹션"]:
                    all_stores[sid]["출처섹션"].append(section)

    # ── Merge ─────────────────────────────────────────────────

    def merge_stores(self, list_a: list[dict], list_b: list[dict]) -> list[dict]:
        merged: dict[str, dict] = {}
        for s in list_a + list_b:
            sid = s["store_id"]
            if sid not in merged:
                merged[sid] = {
                    "store_id": sid,
                    "업체명": s["업체명"],
                    "url": s["url"],
                    "출처섹션": list(s["출처섹션"]),
                    "도매카테고리": list(s["도매카테고리"]),
                }
            else:
                for sec in s["출처섹션"]:
                    if sec not in merged[sid]["출처섹션"]:
                        merged[sid]["출처섹션"].append(sec)
                for c in s["도매카테고리"]:
                    if c not in merged[sid]["도매카테고리"]:
                        merged[sid]["도매카테고리"].append(c)
        return sorted(merged.values(), key=lambda x: x["업체명"])

    # ── Phase 2: 상품 스크래핑 ───────────────────────────────

    async def scrape_store(self, store: dict) -> list[dict]:
        sid = store["store_id"]
        name = store["업체명"]
        url = store["url"]
        products = []

        print(f"\n  [store] {name} (ID:{sid})")
        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            await human_delay(5, 10)
            await handle_bot_challenge(self.page)

            # 업체 전용관 카테고리 탭 파악
            cat_tabs = await self._get_store_categories()
            if not cat_tabs:
                print(f"    → 카테고리 탭 없음, 전체만 수집")
                cat_tabs = ["전체"]

            for cat in cat_tabs:
                try:
                    print(f"    [cat] {cat}")
                    if cat != "전체":
                        await self._click_store_category(cat)
                        await human_delay(3, 5)
                    else:
                        await human_delay(2, 3)

                    expected = await self._get_expected_count()
                    print(f"      → 예상 상품 수: {expected}")

                    await self._scroll_to_load_all(expected)
                    items = await self._extract_products()

                    for item in items:
                        item.update({
                            "출처섹션": "|".join(store["출처섹션"]),
                            "도매카테고리": "|".join(store["도매카테고리"]),
                            "업체명": name,
                            "store_id": sid,
                            "상품카테고리": cat,
                            "수집일": date.today().isoformat(),
                        })
                    products.extend(items)
                    print(f"      → 수집: {len(items)}개 (예상: {expected})")

                    await human_delay(5, 10)

                except Exception as e:
                    print(f"    [cat:{cat}] 오류: {e}")

        except Exception as e:
            print(f"  [store:{name}] 오류: {e}")

        return products

    async def _get_store_categories(self) -> list[str]:
        """업체 전용관의 카테고리 탭 목록 파악 (button, a, div 모두 탐색)"""
        KNOWN_CATS = [
            '전체','일반의약품','전문의약품','의약외상품','건강식품',
            '의료기기','약국용품','동물의약용품','가전/가구','화장품',
            '도서','생활용품','패션잡화','출산/유아동','식품','스포츠/레저'
        ]
        try:
            tabs = await self.page.evaluate(f"""
                () => {{
                    const knownCats = {KNOWN_CATS};
                    // button, a, div 모두 탐색 (바로팜은 div 기반 탭 사용)
                    const candidates = Array.from(document.querySelectorAll('button, a, div, span'));
                    const found = candidates
                        .filter(el => {{
                            const t = el.textContent.trim();
                            return knownCats.includes(t) && el.children.length <= 2;
                        }})
                        .map(el => el.textContent.trim());
                    // 순서 유지하며 중복 제거
                    return [...new Set(found)];
                }}
            """)
            # 대상 카테고리 중 해당 업체에 존재하는 것만 (전체 제외)
            target = set(STORE_SECTION_CATEGORIES + PRODUCT_SECTION_CATEGORIES)
            filtered = [t for t in tabs if t in target]
            print(f"    → 감지된 카테고리 탭: {filtered or tabs}")
            return filtered if filtered else []
        except Exception as e:
            print(f"    [카테고리 탭 파악 오류] {e}")
            return []

    async def _click_store_category(self, cat: str):
        """카테고리 탭 클릭 — button, a, div 모두 시도"""
        selectors = [
            f'button:has-text("{cat}")',
            f'a:has-text("{cat}")',
            f'div:has-text("{cat}")',
            f'span:has-text("{cat}")',
        ]
        for sel in selectors:
            try:
                tabs = await self.page.query_selector_all(sel)
                for tab in tabs:
                    # 텍스트가 정확히 일치하는 요소만 (has-text는 포함 검색)
                    t = (await tab.text_content() or "").strip()
                    if t != cat:
                        continue
                    if not await tab.is_visible():
                        continue
                    await tab.scroll_into_view_if_needed()
                    await human_delay(0.3, 0.8)
                    await tab.click()
                    await human_delay(1, 2)
                    return
            except Exception:
                continue
        raise Exception(f"카테고리 탭 '{cat}' 클릭 실패")

    async def _get_expected_count(self) -> int:
        try:
            count_text = await self.page.evaluate("""() => {
                // <p><em>N</em>개 상품</p> 구조
                const ems = Array.from(document.querySelectorAll('p > em, span > em'));
                for (const em of ems) {
                    const parent = em.parentElement;
                    if (parent && parent.textContent.includes('개 상품')) {
                        return em.textContent.trim();
                    }
                }
                // 폴백: 텍스트 패턴 검색
                const all = document.body.innerText;
                const m = all.match(/(\\d[\\d,]*)\\s*개\\s*상품/);
                return m ? m[1] : '0';
            }""")
            return int(count_text.replace(",", ""))
        except Exception:
            return 0

    async def _scroll_to_load_all(self, expected: int, max_scrolls: int = 150):
        """무한 스크롤로 전체 상품을 로드
        상품 카드 수 카운팅: 가격을 포함한 p 태그 수로 추정
        """
        prev_count = 0
        stable = 0
        for i in range(max_scrolls):
            # 상품 카드 카운트: 가격 텍스트를 가진 p 태그 수 (대략적 추정)
            current = await self.page.evaluate("""() => {
                // 품절 또는 숫자원 패턴을 가진 p 태그 수
                return Array.from(document.querySelectorAll('p')).filter(p => {
                    const t = p.textContent.trim();
                    return t === '품절' || /^[\\d,]+$/.test(t) || /^[\\d,]+원$/.test(t);
                }).length;
            }""")
            if expected > 0 and current >= expected:
                print(f"      스크롤 {i+1}회 — {current}/{expected} 로드 완료")
                break
            if current == prev_count:
                stable += 1
                if stable >= 5:
                    print(f"      스크롤 {i+1}회 — 변화 없음 5회 연속, 중단 ({current}/{expected})")
                    break
            else:
                stable = 0
            prev_count = current
            scroll_px = random.randint(400, 700)
            await self.page.mouse.wheel(0, scroll_px)
            await asyncio.sleep(random.uniform(1.5, 2.5))

    async def _extract_products(self) -> list[dict]:
        """상품 카드에서 상품명, 규격, 가격 추출
        
        DOM 구조 (바로팜 업체 전용관):
          카드 컨테이너 (div)
            └── p: 상품명
            └── p: 규격 (없는 경우 있음)
            └── p: 가격 숫자 (쉼표 포함) + span: '원'
               또는 strong/p: '품절'
        """
        return await self.page.evaluate("""() => {
            const results = [];
            const seen = new Set();
            const SKIP_TEXTS = new Set([
                '전체','일반의약품','전문의약품','의약외상품','건강식품',
                '의료기기','약국용품','동물의약용품','화장품','생활용품',
                '식품','스포츠/레저','도서','패션잡화','출산/유아동','가전/가구',
                '추천순','신상품순','낮은가격순','높은가격순','장바구니','구매',
                '쿠폰','품절','원','개 상품',
            ]);

            // 가격을 포함하는 p태그를 기준으로 상위 카드 컨테이너 탐색
            const pricePTags = Array.from(document.querySelectorAll('p')).filter(p => {
                const t = p.textContent.trim();
                // 숫자,숫자 형태의 가격 또는 품절
                return /^[\\d,]+$/.test(t) || t === '품절';
            });

            for (const priceEl of pricePTags) {
                // 카드 컨테이너: 가격 p태그에서 2~4단계 위 부모
                let card = priceEl.parentElement;
                for (let i = 0; i < 3; i++) {
                    if (!card) break;
                    // 상품명 p태그가 같은 카드 안에 있으면 해당 레벨이 카드
                    const pTags = Array.from(card.querySelectorAll('p'));
                    if (pTags.length >= 2) break;
                    card = card.parentElement;
                }
                if (!card) continue;

                // 카드 내 모든 p 태그 텍스트 수집 (순서대로)
                const pTexts = Array.from(card.querySelectorAll('p'))
                    .map(p => p.textContent.trim())
                    .filter(t => t.length > 0);

                let productName = '';
                let spec = '';
                let price = 0;
                let isSoldOut = false;

                for (const t of pTexts) {
                    if (t === '품절') { isSoldOut = true; continue; }
                    // 가격: 숫자만 또는 숫자+원
                    const priceMatch = t.match(/^([\\d,]+)원?$/);
                    if (priceMatch) {
                        price = parseInt(priceMatch[1].replace(/,/g, ''));
                        continue;
                    }
                    if (SKIP_TEXTS.has(t)) continue;
                    // 첫 번째 유효 텍스트 = 상품명
                    if (!productName && t.length > 1 && t.length < 200) {
                        productName = t;
                    } else if (productName && !spec && t.length > 0 && t.length < 100) {
                        spec = t;
                    }
                }

                if (!productName) continue;
                if (price === 0 && !isSoldOut) continue;

                const key = `${productName}||${spec}||${price}`;
                if (seen.has(key)) continue;
                seen.add(key);

                results.push({
                    상품명: productName,
                    규격: spec,
                    가격: price,
                    품절여부: isSoldOut,
                });
            }
            return results;
        }""")

    # ── 저장 ─────────────────────────────────────────────────

    def save(self, products: list[dict], filename: str | None = None) -> Path:
        out_dir = BASE_DIR / "data" / "baropharm" / "products"
        out_dir.mkdir(parents=True, exist_ok=True)
        if filename is None:
            ym = date.today().strftime("%y%m")
            filename = f"{ym}_baropharm_products.csv"
        out_path = out_dir / filename
        fieldnames = [
            "출처섹션", "도매카테고리", "업체명", "store_id",
            "상품카테고리", "상품명", "규격", "가격", "품절여부", "수집일",
        ]
        mode = "a" if out_path.exists() else "w"
        with out_path.open(mode, newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if mode == "w":
                writer.writeheader()
            writer.writerows(products)
        return out_path

    # ── 메인 실행 ─────────────────────────────────────────────

    async def run(self) -> list[dict]:
        try:
            await self.start_browser()
            print("=" * 60)
            print("[바로팜 상품 스크래퍼] 시작")
            print("=" * 60)

            await self.login()
            await handle_bot_challenge(self.page)

            if self.target_store_id:
                store_list = [{
                    "store_id": self.target_store_id,
                    "업체명": f"store_{self.target_store_id}",
                    "url": STORE_URL_TMPL.format(store_id=self.target_store_id),
                    "출처섹션": ["수동지정"],
                    "도매카테고리": ["수동지정"],
                }]
            else:
                store_list = await self.collect_all_stores()
                print(f"\n[Phase1 완료] 총 {len(store_list)}개 업체 수집")

            if self.max_stores:
                store_list = store_list[:self.max_stores]
                print(f"[max_stores] {self.max_stores}개로 제한")

            total = len(store_list)
            out_path = None

            for i, store in enumerate(store_list, 1):
                print(f"\n[{i}/{total}] {store['업체명']}")
                products = await self.scrape_store(store)
                self.all_products.extend(products)

                if products:
                    out_path = self.save(products)
                    print(f"  → {len(products)}개 저장: {out_path}")

                if i < total:
                    await self._delay()

            print(f"\n{'='*60}")
            print(f"[완료] 총 {len(self.all_products)}개 상품 수집")
            if out_path:
                print(f"[출력] {out_path}")
            print("=" * 60)

            return self.all_products

        finally:
            await self.stop_browser()
