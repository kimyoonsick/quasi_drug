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
STORE_LIST_CSV = BASE_DIR / "data" / "baropharm" / "products" / "260516_바로팜_외품업체리스트 - 시트1.csv"


class BaropharmProductScraper:
    name = "baropharm_product"
    delay_min = 15.0
    delay_max = 30.0

    def __init__(self, headless: bool = False, max_stores: int | None = None,
                 target_store_id: str | None = None,
                 store_csv: str | Path | None = None):
        self.headless = headless
        self.max_stores = max_stores
        self.target_store_id = target_store_id
        self.store_csv = Path(store_csv) if store_csv else STORE_LIST_CSV
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

        await self.page.goto(WHOLESALERS_URL, wait_until="domcontentloaded")
        await human_delay(5, 8)
        await human_delay(3, 5)
        await handle_bot_challenge(self.page)

        # 로그인 체크
        url_now = self.page.url
        print(f"  [Phase1] 현재 URL: {url_now}")
        if "signin" in url_now or "login" in url_now:
            print("  [Phase1] 재로그인")
            await self.login()
            await self.page.goto(WHOLESALERS_URL, wait_until="domcontentloaded")
            await human_delay(5, 8)
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
        }""")
        await human_delay(1, 2)

        # 맨 위로 복귀
        await self.page.evaluate("window.scrollTo(0, 0)")
        await human_delay(1, 2)

        # 섹션 존재 여부 확인
        section_check = await self.page.evaluate("""() => ({
            storeExists: !!document.querySelector('#store'),
            wholesalersExists: !!document.querySelector('#wholesalers'),
            storeListExists: !!document.querySelector('#store .wholesalers-container__contents__section__list'),
            wholesalersListExists: !!document.querySelector('#wholesalers .wholesalers-container__contents__section__list'),
        })""")
        print(f"  [Phase1] 섹션 확인: {section_check}")

        # ── Phase 1A: 바로팜 스토어 (#store) ──
        print("\n[Phase 1A] 바로팜 스토어 섹션")
        await self._scroll_to_container("#store")
        await human_delay(2, 3)

        for cat in STORE_SECTION_CATEGORIES:
            try:
                print(f"  [1A] {cat}")
                clicked = await self._click_tab_in_section("#store", cat)
                if not clicked:
                    continue
                await human_delay(2, 3)
                new = await self._extract_stores_from_section("#store", "바로팜스토어", cat)
                self._merge_into(all_stores, new, "바로팜스토어", cat)
                print(f"    → {len(new)}개 업체")
                await human_delay(2, 4)
            except Exception as e:
                print(f"  [1A] {cat} 오류: {e}")

        # ── Phase 1B: 의약외품 (#wholesalers) ──
        print("\n[Phase 1B] 의약외품 섹션")

        # 팝업 재제거 (Phase 1A에서 페이지 복구 후 다시 뜰 수 있음)
        await self.page.evaluate("""() => {
            const all = Array.from(document.querySelectorAll('*'));
            for (const el of all) {
                if (el.textContent.trim() === '오늘 하루 보지 않기') {
                    let t = el;
                    for (let j = 0; j < 5; j++) {
                        if (t.parentElement && t.parentElement !== document.body) t = t.parentElement;
                    }
                    t.remove(); break;
                }
            }
        }""")
        await human_delay(1, 2)

        # #wholesalers까지 스크롤
        await self._scroll_to_container("#wholesalers")
        await human_delay(2, 3)

        # 디버그: 현재 섹션 상태
        ws_debug = await self.page.evaluate("""() => {
            const sec = document.querySelector('#wholesalers');
            if (!sec) return {exists: false};
            const tabs = Array.from(sec.querySelectorAll('button,div,span,a'))
                .filter(el => el.children.length <= 1 && el.offsetParent !== null)
                .map(el => el.textContent.trim())
                .filter(t => t.length > 0 && t.length < 20);
            return {exists: true, tabs: tabs.slice(0, 20)};
        }""")
        print(f"  [1B-debug] #wholesalers: {ws_debug}")

        # 이름순 정렬 (#wholesalers 내부의 이름순 버튼)
        sorted_ok = await self.page.evaluate("""() => {
            const sec = document.querySelector('#wholesalers');
            if (!sec) return false;
            const btns = Array.from(sec.querySelectorAll('*'));
            for (const b of btns) {
                if (b.textContent.trim() === '이름순' && b.children.length <= 1) {
                    b.click(); return true;
                }
            }
            return false;
        }""")
        print(f"  [1B] 이름순: {'적용' if sorted_ok else '없음'}")
        await human_delay(2, 3)

        try:
            print(f"  [1B] 전체 업체 추출")
            # 탭 클릭 없음. 전체 목록 수집
            new = await self._extract_stores_from_section("#wholesalers", "의약외품", "전체", "전체")
            self._merge_into(all_stores, new, "의약외품", "전체")
            print(f"    → {len(new)}개 업체")
            await human_delay(2, 4)
        except Exception as e:
            print(f"  [1B] 오류: {e}")

        return sorted(all_stores.values(), key=lambda x: x["업체명"])

    async def _scroll_to_container(self, css_id: str):
        """CSS ID 요소까지 스크롤"""
        await self.page.evaluate(f"""() => {{
            const el = document.querySelector('{css_id}');
            if (el) el.scrollIntoView({{behavior:'smooth', block:'start'}});
        }}""")
        await human_delay(2, 3)

    async def _click_tab_in_section(self, section_sel: str, cat_name: str) -> bool:
        """섹션 내부의 카테고리 탭 클릭"""
        result = await self.page.evaluate(f"""() => {{
            const sec = document.querySelector('{section_sel}');
            if (!sec) return {{ok:false, n:0, reason:'섹션없음'}};
            const cands = Array.from(sec.querySelectorAll('button,div,span,a'))
                .filter(el => el.textContent.trim() === '{cat_name}'
                    && el.children.length <= 1 && el.offsetParent !== null);
            if (cands.length > 0) {{
                cands[0].click();
                return {{ok:true, n:cands.length}};
            }}
            return {{ok:false, n:0, reason:'탭없음'}};
        }}""")
        if result["ok"]:
            print(f"    탭 클릭 ({result['n']}개)")
        else:
            print(f"    탭 '{cat_name}' 없음 ({result.get('reason','')})")
        return result["ok"]

    async def _extract_stores_from_section(self, section_sel: str, section_name: str,
                                            cat: str, cat_name: str = "") -> list[dict]:
        """섹션의 업체 리스트에서 업체명 추출 후 개별 클릭으로 URL 수집"""
        if not cat_name:
            cat_name = cat

        # 1단계: 업체 이름 일괄 추출
        names = await self.page.evaluate(f"""() => {{
            const sec = document.querySelector('{section_sel}');
            if (!sec) return [];
            const lc = sec.querySelector('.wholesalers-container__contents__section__list');
            if (!lc) return [];
            return Array.from(lc.children).map(child => {{
                const p = child.querySelector('.brand_name');
                if (!p) return null;
                let name = '';
                for (const node of p.childNodes) {{
                    if (node.nodeType === 3) name += node.textContent;
                }}
                return name.trim() || null;
            }}).filter(Boolean);
        }}""")

        if not names:
            print(f"    [DEBUG] 업체명 0개 추출됨")
            return []

        print(f"    업체명 {len(names)}개 추출, 개별 클릭으로 URL 수집 시작")
        results = []

        for i, name in enumerate(names):
            try:
                clicked = await self.page.evaluate(f"""() => {{
                    const sec = document.querySelector('{section_sel}');
                    if (!sec) return false;
                    const lc = sec.querySelector('.wholesalers-container__contents__section__list');
                    if (!lc || !lc.children[{i}]) return false;
                    lc.children[{i}].click();
                    return true;
                }}""")

                if not clicked:
                    continue

                await human_delay(2, 3)

                new_url = self.page.url
                if i < 3:
                    print(f"    [{i}] 클릭 후 URL: {new_url}")

                sid = None
                store_url = new_url
                m = re.search(r'/quasi-drug-mall/(\d+)', new_url)
                if m:
                    sid = m.group(1)
                else:
                    m = re.search(r'/brand/([^/?#]+)', new_url)
                    if m:
                        sid = m.group(1)

                if sid:
                    results.append({
                        "store_id": sid,
                        "업체명": name,
                        "url": store_url,
                        "출처섹션": [section_name],
                        "도매카테고리": [cat],
                    })

                # wholesalers 페이지로 복구
                await self.page.goto(WHOLESALERS_URL, wait_until="domcontentloaded")
                await human_delay(3, 5)

                # 팝업 제거
                await self.page.evaluate("""() => {
                    const all = Array.from(document.querySelectorAll('*'));
                    for (const el of all) {
                        if (el.textContent.trim() === '오늘 하루 보지 않기') {
                            let t = el;
                            for (let j = 0; j < 5; j++) {
                                if (t.parentElement && t.parentElement !== document.body) t = t.parentElement;
                            }
                            t.remove(); break;
                        }
                    }
                }""")

                # 카테고리 탭 재클릭 (복구 후 기본 탭으로 돌아가므로)
                if section_sel == "#wholesalers":
                    # 이름순 정렬 재적용
                    await self.page.evaluate("""() => {
                        const sec = document.querySelector('#wholesalers');
                        if (!sec) return false;
                        const btns = Array.from(sec.querySelectorAll('*'));
                        for (const b of btns) {
                            if (b.textContent.trim() === '이름순' && b.children.length <= 1) {
                                b.click(); return true;
                            }
                        }
                        return false;
                    }""")
                    await human_delay(1, 2)
                else:
                    await self._click_tab_in_section(section_sel, cat_name)
                    await human_delay(1, 2)

            except Exception as e:
                print(f"    [{i}] {name} 오류: {e}")
                try:
                    await self.page.goto(WHOLESALERS_URL, wait_until="domcontentloaded")
                    await human_delay(3, 5)
                except Exception:
                    pass

        print(f"    → URL 수집 완료: {len(results)}개")
        return results

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

    def _is_mall_type(self, url: str) -> bool:
        return "quasi-drug-mall/" in url

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

            if self._is_mall_type(url):
                products = await self._scrape_mall_store(store)
            else:
                products = await self._scrape_brand_store(store)

        except Exception as e:
            print(f"  [store:{name}] 오류: {e}")

        return products

    async def _scrape_brand_store(self, store: dict) -> list[dict]:
        sid = store["store_id"]
        name = store["업체명"]
        url = store["url"]
        products = []

        cat_tabs = await self._get_store_categories()

        if not cat_tabs:
            print(f"    → 카테고리 탭 없음, 전체만 수집")
            cat_tabs = [{"index": 0, "name": "전체"}]

        for tab in cat_tabs:
            cat_name = tab["name"]
            cat_idx = tab["index"]
            try:
                print(f"    [cat] {cat_name}")
                if cat_name != "전체":
                    # 탭 영역 존재 여부 확인 — 이전 카테고리에서 사라졌을 수 있음
                    tabs_exist = await self.page.evaluate(
                        "!!document.querySelector('.brand-product-list ul')")
                    if not tabs_exist:
                        print(f"      → 탭 영역 사라짐, 페이지 재로드")
                        await self.page.goto(url, wait_until="domcontentloaded")
                        await human_delay(3, 5)
                        await handle_bot_challenge(self.page)

                    await self._click_store_category_by_index(cat_idx)
                    await human_delay(3, 5)
                else:
                    await human_delay(2, 3)

                expected = await self._get_expected_count()
                print(f"      → 예상 상품 수: {expected}")

                if expected == 0 and cat_name != "전체":
                    print(f"      → 상품 0개, 스킵")
                    continue

                await self._scroll_to_load_all(expected)
                items = await self._extract_products()

                for item in items:
                    item.update({
                        "카테고리1": store.get("카테고리1", ""),
                        "카테고리2": store.get("카테고리2", ""),
                        "업체명": name,
                        "store_id": sid,
                        "상품카테고리": cat_name,
                        "수집일": date.today().isoformat(),
                    })
                products.extend(items)
                print(f"      → 수집: {len(items)}개 (예상: {expected})")

                await human_delay(5, 10)

            except Exception as e:
                print(f"    [cat:{cat_name}] 오류: {e}")

        return products

    # ── quasi-drug-mall 전용 로직 ──────────────────────────────

    async def _scrape_mall_store(self, store: dict) -> list[dict]:
        sid = store["store_id"]
        name = store["업체명"]
        url = store["url"]
        products = []

        # 중분류(depth-1) 카테고리 파악
        major_cats = await self._get_mall_major_categories()

        if not major_cats:
            print(f"    → 중분류 카테고리 없음, 전체만 수집")
            major_cats = [{"index": 0, "name": "전체"}]

        for major in major_cats:
            major_name = major["name"]
            major_idx = major["index"]
            try:
                print(f"    [중분류] {major_name}")
                if major_name != "전체":
                    await self._click_mall_major_category(major_idx)
                    await human_delay(2, 4)

                # 소분류(depth-2) 카테고리 파악
                minor_cats = await self._get_mall_minor_categories()

                if not minor_cats:
                    # 소분류 없으면 현재 중분류 그대로 수집
                    minor_cats = [{"index": -1, "name": "전체"}]

                for minor in minor_cats:
                    minor_name = minor["name"]
                    minor_idx = minor["index"]
                    try:
                        print(f"      [소분류] {minor_name}")
                        if minor_idx >= 0 and minor_name != "전체":
                            await self._click_mall_minor_category(minor_idx)
                            await human_delay(2, 4)

                        expected = await self._get_expected_count()
                        print(f"        → 예상 상품 수: {expected}")

                        if expected == 0:
                            print(f"        → 상품 0개, 스킵")
                            continue

                        # 더보기 버튼으로 전체 로드
                        await self._load_all_mall_products(expected)
                        items = await self._extract_mall_products()

                        for item in items:
                            item.update({
                                "카테고리1": store.get("카테고리1", ""),
                                "카테고리2": store.get("카테고리2", ""),
                                "업체명": name,
                                "store_id": sid,
                                "상품카테고리": major_name,
                                "상품소분류": minor_name if minor_name != "전체" else "",
                                "수집일": date.today().isoformat(),
                            })
                        products.extend(items)
                        print(f"        → 수집: {len(items)}개 (예상: {expected})")

                        await human_delay(3, 6)

                    except Exception as e:
                        print(f"      [소분류:{minor_name}] 오류: {e}")

                await human_delay(2, 4)

            except Exception as e:
                print(f"    [중분류:{major_name}] 오류: {e}")

        return products

    async def _get_mall_major_categories(self) -> list[dict]:
        """의약외품 전용관 중분류(depth-1) 카테고리

        DOM: div.area.category div.depth-1 > div
        첫 번째 = 전체 (스킵)
        """
        try:
            tabs = await self.page.evaluate(r"""
                () => {
                    const d1 = document.querySelector('.area.category .depth-1');
                    if (!d1) return [];
                    const items = Array.from(d1.querySelectorAll(':scope > div'));
                    const result = [];
                    for (let i = 0; i < items.length; i++) {
                        if (i === 0) continue;
                        const name = items[i].textContent.trim();
                        if (!name || name.length === 0) continue;
                        result.push({index: i, name: name});
                    }
                    return result;
                }
            """)
            if tabs:
                names = [t["name"] for t in tabs]
                print(f"    → 중분류 탭: {names}")
            return tabs
        except Exception as e:
            print(f"    [중분류 탭 파악 오류] {e}")
            return []

    async def _get_mall_minor_categories(self) -> list[dict]:
        """의약외품 전용관 소분류(depth-2) 카테고리

        DOM: div.area.category div.depth-2 > div
        첫 번째 = 전체 (스킵)
        총 개수를 먼저 파악한 후 반환
        """
        try:
            tabs = await self.page.evaluate(r"""
                () => {
                    const d2 = document.querySelector('.area.category .depth-2');
                    if (!d2) return [];
                    const items = Array.from(d2.querySelectorAll(':scope > div'));
                    const result = [];
                    for (let i = 0; i < items.length; i++) {
                        if (i === 0) continue;
                        const name = items[i].textContent.trim();
                        if (!name || name.length === 0) continue;
                        result.push({index: i, name: name});
                    }
                    return result;
                }
            """)
            if tabs:
                names = [t["name"] for t in tabs]
                print(f"      → 소분류 탭 ({len(tabs)}개): {names}")
            return tabs
        except Exception as e:
            print(f"      [소분류 탭 파악 오류] {e}")
            return []

    async def _click_mall_major_category(self, idx: int):
        """중분류(depth-1) 카테고리 클릭"""
        clicked = await self.page.evaluate(f"""
            () => {{
                const d1 = document.querySelector('.area.category .depth-1');
                if (!d1) return false;
                const items = Array.from(d1.querySelectorAll(':scope > div'));
                if ({idx} >= items.length) return false;
                items[{idx}].click();
                return true;
            }}
        """)
        if not clicked:
            raise Exception(f"중분류 탭 인덱스 {idx} 클릭 실패")
        await human_delay(1, 2)

    async def _click_mall_minor_category(self, idx: int):
        """소분류(depth-2) 카테고리 클릭"""
        clicked = await self.page.evaluate(f"""
            () => {{
                const d2 = document.querySelector('.area.category .depth-2');
                if (!d2) return false;
                const items = Array.from(d2.querySelectorAll(':scope > div'));
                if ({idx} >= items.length) return false;
                items[{idx}].click();
                return true;
            }}
        """)
        if not clicked:
            raise Exception(f"소분류 탭 인덱스 {idx} 클릭 실패")
        await human_delay(1, 2)

    async def _load_all_mall_products(self, expected: int, max_clicks: int = 200):
        """'상품 더보기' 버튼을 반복 클릭하여 전체 상품 로드"""
        for i in range(max_clicks):
            # 현재 상품 수 확인
            current = await self.page.evaluate(r"""
                () => {
                    const c = document.querySelector('.area.products-container');
                    if (!c) return 0;
                    return c.querySelectorAll(':scope > div').length;
                }
            """)
            if expected > 0 and current >= expected:
                print(f"        로드 완료: {current}/{expected}")
                break

            # 더보기 버튼 클릭 시도
            clicked = await self.page.evaluate(r"""
                () => {
                    const btn = document.querySelector('.area.more-button button');
                    if (!btn) return false;
                    if (btn.offsetParent === null) return false;
                    btn.click();
                    return true;
                }
            """)
            if not clicked:
                print(f"        더보기 버튼 없음, 로드 완료: {current}/{expected}")
                break

            if (i + 1) % 10 == 0:
                print(f"        더보기 {i+1}회 — {current}/{expected}")

            await asyncio.sleep(random.uniform(1.0, 2.0))

    async def _extract_mall_products(self) -> list[dict]:
        """quasi-drug-mall 상품 추출

        DOM:
          div.area.products-container > div (상품 카드)
            div.product-name-box > p.txt-name       → 상품명
            div.product-name-box > p.meta-text > span:nth(1) → 규격
            div.product-name-box > p.meta-text > span:nth(2) → 단위수량
            div.product-name-box > p.meta-text > span:nth(3) → 단위
            div.price-box > p.price-txt              → 할인후금액
            div.price-box > p.normal-price-txt       → 할인전금액
            div.price-box > p (단독)                   → 할인없는 가격
            div.price-box > strong                   → 품절
        """
        return await self.page.evaluate(r"""
            () => {
                const results = [];
                const seen = new Set();
                const container = document.querySelector('.area.products-container');
                if (!container) return results;
                const cards = Array.from(container.querySelectorAll(':scope > div'));

                for (const card of cards) {
                    // 상품명
                    const nameEl = card.querySelector('.txt-name');
                    if (!nameEl) continue;
                    const productName = nameEl.textContent.trim();
                    if (!productName) continue;

                    // 규격, 단위수량, 단위
                    const metaSpans = card.querySelectorAll('.meta-text span');
                    const spec = metaSpans[0] ? metaSpans[0].textContent.trim() : '';
                    const unitQty = metaSpans[1] ? metaSpans[1].textContent.trim() : '';
                    const unit = metaSpans[2] ? metaSpans[2].textContent.trim() : '';

                    // 가격 처리
                    const priceBox = card.querySelector('.price-box');
                    let price = 0;
                    let originalPrice = 0;
                    let discountRate = '';
                    let isSoldOut = false;

                    if (priceBox) {
                        // 품절 체크
                        const soldOutEl = priceBox.querySelector('strong');
                        if (soldOutEl && soldOutEl.textContent.trim() === '품절') {
                            isSoldOut = true;
                        }

                        // 할인후 가격
                        const priceTxt = priceBox.querySelector('.price-txt');
                        if (priceTxt) {
                            const m = priceTxt.textContent.match(/([\d,]+)/);
                            if (m) price = parseInt(m[1].replace(/,/g, ''));
                        }

                        // 할인전 가격
                        const normalTxt = priceBox.querySelector('.normal-price-txt');
                        if (normalTxt) {
                            const m = normalTxt.textContent.match(/([\d,]+)/);
                            if (m) originalPrice = parseInt(m[1].replace(/,/g, ''));
                        }

                        // 할인 없는 단순 가격 (p 태그 하나만 있는 경우)
                        if (price === 0 && !isSoldOut) {
                            const allP = priceBox.querySelectorAll('p');
                            for (const p of allP) {
                                const m = p.textContent.match(/([\d,]+)/);
                                if (m) {
                                    price = parseInt(m[1].replace(/,/g, ''));
                                    break;
                                }
                            }
                        }
                    }

                    // 할인율: meta-text 또는 전체 텍스트에서 추출
                    const fullText = card.textContent || '';
                    const drMatch = fullText.match(/(\d+)\s*%/);
                    if (drMatch) discountRate = drMatch[1] + '%';

                    if (!productName) continue;

                    const key = `${productName}||${spec}||${price}`;
                    if (seen.has(key)) continue;
                    seen.add(key);

                    results.push({
                        '상품명': productName,
                        '규격': spec,
                        '단위수량': unitQty,
                        '단위': unit,
                        '할인율': discountRate,
                        '가격': price,
                        '할인전가격': originalPrice,
                        '품절여부': isSoldOut,
                    });
                }
                return results;
            }
        """)

    async def _get_store_categories(self) -> list[dict]:
        """업체 전용관의 카테고리 탭 목록 파악

        DOM 구조:
          div.brand-product-list > ul > li (카테고리 버튼)
            li:nth-child(1) = 전체 (스킵)
            li:nth-child(2+) = 개별 카테고리
              - li 클래스에 POINTER가 있으면 클릭 가능
              - li > span = 카테고리명

        Returns:
            [{"index": 1, "name": "의약외품"}, ...] (전체 제외, 클릭 가능한 것만)
        """
        try:
            tabs = await self.page.evaluate("""
                () => {
                    const ul = document.querySelector('.brand-product-list ul');
                    if (!ul) return [];
                    const items = Array.from(ul.querySelectorAll(':scope > li'));
                    const result = [];
                    for (let i = 0; i < items.length; i++) {
                        const li = items[i];
                        const span = li.querySelector('span');
                        const name = span ? span.textContent.trim() : li.textContent.trim();
                        // 첫 번째(전체) 스킵, POINTER 없는 빈자리 스킵
                        if (i === 0) continue;
                        if (!li.className.includes('POINTER')) continue;
                        if (!name || name.length === 0) continue;
                        result.push({index: i, name: name});
                    }
                    return result;
                }
            """)
            if tabs:
                names = [t["name"] for t in tabs]
                print(f"    → 카테고리 탭: {names}")
            return tabs
        except Exception as e:
            print(f"    [카테고리 탭 파악 오류] {e}")
            return []

    async def _click_store_category_by_index(self, idx: int):
        """카테고리 탭을 li 인덱스로 클릭"""
        clicked = await self.page.evaluate(f"""
            () => {{
                const ul = document.querySelector('.brand-product-list ul');
                if (!ul) return false;
                const items = Array.from(ul.querySelectorAll(':scope > li'));
                if ({idx} >= items.length) return false;
                items[{idx}].click();
                return true;
            }}
        """)
        if not clicked:
            raise Exception(f"카테고리 탭 인덱스 {idx} 클릭 실패")
        await human_delay(1, 2)

    async def _get_expected_count(self) -> int:
        try:
            count_text = await self.page.evaluate(r"""() => {
                // brand: div.total-txt-box span > em
                const ttb = document.querySelector('.total-txt-box span > em');
                if (ttb) return ttb.textContent.trim();

                // mall: span.txt-total > em
                const mallEm = document.querySelector('.txt-total em');
                if (mallEm) return mallEm.textContent.trim();

                // 다른 구조: p > em, span > em
                const ems = Array.from(document.querySelectorAll('p > em, span > em'));
                for (const em of ems) {
                    const parent = em.parentElement;
                    if (parent && parent.textContent.includes('개 상품')) {
                        return em.textContent.trim();
                    }
                }
                // 폴백: 텍스트 패턴 검색
                const all = document.body.innerText;
                const m = all.match(/(\d[\d,]*)\s*개\s*상품/);
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
            current = await self.page.evaluate(r"""() => {
                // brand-prod-list 기반 카운트
                const ul = document.querySelector('.brand-prod-list ul');
                if (ul) return ul.querySelectorAll(':scope > li').length;
                // 폴백: 품절 또는 숫자원 패턴 p 태그 수
                return Array.from(document.querySelectorAll('p')).filter(p => {
                    const t = p.textContent.trim();
                    return t === '품절' || /^[\d,]+$/.test(t) || /^[\d,]+원$/.test(t);
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
          div.brand-prod-list > ul > li (상품 카드)
            카드 내 p 태그들:
              p: 상품명
              p: 규격
              p: 가격 (숫자 + '원')
              또는 '품절'
        """
        return await self.page.evaluate(r"""() => {
            const results = [];
            const seen = new Set();
            const SKIP_TEXTS = new Set([
                '전체','일반의약품','전문의약품','의약외상품','건강식품',
                '의료기기','약국용품','동물의약용품','화장품','생활용품',
                '식품','스포츠/레저','도서','패션잡화','출산/유아동','가전/가구',
                '추천순','신상품순','낮은가격순','높은가격순','장바구니','구매',
                '쿠폰','품절','원','개 상품',
            ]);

            // brand-prod-list > ul > li 기반 탐색
            const prodList = document.querySelector('.brand-prod-list ul');
            if (prodList) {
                const cards = Array.from(prodList.querySelectorAll(':scope > li'));
                for (const card of cards) {
                    // li 전체 텍스트에서 품절 여부 확인
                    const fullText = card.textContent || '';
                    let isSoldOut = fullText.includes('품절');

                    // p 태그 텍스트 수집
                    const pTexts = Array.from(card.querySelectorAll('p'))
                        .map(p => p.textContent.trim())
                        .filter(t => t.length > 0);

                    let productName = '';
                    let spec = '';
                    let price = 0;

                    for (const t of pTexts) {
                        if (t === '품절') continue;
                        const priceMatch = t.match(/^([\d,]+)\s*원?$/);
                        if (priceMatch) {
                            price = parseInt(priceMatch[1].replace(/,/g, ''));
                            continue;
                        }
                        if (SKIP_TEXTS.has(t)) continue;
                        if (!productName && t.length > 1 && t.length < 200) {
                            productName = t;
                        } else if (productName && !spec && t.length > 0 && t.length < 100) {
                            spec = t;
                        }
                    }

                    // p 태그에서 가격 못 찾은 경우, 전체 텍스트에서 시도
                    if (price === 0 && !isSoldOut) {
                        const m = fullText.match(/([\d,]+)\s*원/);
                        if (m) price = parseInt(m[1].replace(/,/g, ''));
                    }

                    if (!productName) continue;

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
            }

            // 폴백: p 태그 기반 탐색
            const pricePTags = Array.from(document.querySelectorAll('p')).filter(p => {
                const t = p.textContent.trim();
                return /^[\d,]+$/.test(t) || t === '품절';
            });

            for (const priceEl of pricePTags) {
                let card = priceEl.parentElement;
                for (let i = 0; i < 3; i++) {
                    if (!card) break;
                    const pTags = Array.from(card.querySelectorAll('p'));
                    if (pTags.length >= 2) break;
                    card = card.parentElement;
                }
                if (!card) continue;

                const pTexts = Array.from(card.querySelectorAll('p'))
                    .map(p => p.textContent.trim())
                    .filter(t => t.length > 0);

                let productName = '';
                let spec = '';
                let price = 0;
                let isSoldOut = false;

                for (const t of pTexts) {
                    if (t === '품절') { isSoldOut = true; continue; }
                    const priceMatch = t.match(/^([\d,]+)원?$/);
                    if (priceMatch) {
                        price = parseInt(priceMatch[1].replace(/,/g, ''));
                        continue;
                    }
                    if (SKIP_TEXTS.has(t)) continue;
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
            "카테고리1", "카테고리2", "업체명", "store_id",
            "상품카테고리", "상품소분류", "상품명", "규격", "단위수량", "단위",
            "할인율", "가격", "할인전가격", "품절여부", "수집일",
        ]
        mode = "a" if out_path.exists() else "w"
        with out_path.open(mode, newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if mode == "w":
                writer.writeheader()
            writer.writerows(products)
        return out_path

    # ── 메인 실행 ─────────────────────────────────────────────

    def load_store_list_from_csv(self) -> list[dict]:
        """CSV 파일에서 업체 리스트 로드

        CSV 컬럼: 카테고리1, 카테고리2, 업체명, URL, Store_id
        URL + Store_id를 결합하여 전체 URL 생성
        """
        csv_path = self.store_csv
        if not csv_path.exists():
            raise FileNotFoundError(f"업체 리스트 CSV 없음: {csv_path}")

        stores = []
        with csv_path.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = (row.get("Store_id") or "").strip()
                if not sid:
                    continue
                url_base = (row.get("URL") or "").strip().rstrip("/")
                url = f"{url_base}/{sid}"
                stores.append({
                    "store_id": sid,
                    "업체명": (row.get("업체명") or "").strip(),
                    "url": url,
                    "카테고리1": (row.get("카테고리1") or "").strip(),
                    "카테고리2": (row.get("카테고리2") or "").strip(),
                })
        print(f"  [CSV] {csv_path.name}에서 {len(stores)}개 업체 로드")
        return stores

    async def run(self) -> list[dict]:
        try:
            await self.start_browser()
            print("=" * 60)
            print("[바로팜 상품 스크래퍼] 시작")
            print("=" * 60)

            await self.login()
            await handle_bot_challenge(self.page)

            if self.target_store_id:
                # CSV에서 업체명 조회
                store_name = f"store_{self.target_store_id}"
                cat1 = "수동지정"
                cat2 = ""
                try:
                    csv_stores = self.load_store_list_from_csv()
                    for s in csv_stores:
                        if s["store_id"] == self.target_store_id:
                            store_name = s["업체명"]
                            cat1 = s.get("카테고리1", "수동지정")
                            cat2 = s.get("카테고리2", "")
                            break
                except Exception:
                    pass

                # 숫자 ID면 quasi-drug-mall, 아니면 brand
                if self.target_store_id.isdigit():
                    url = f"https://www.baropharm.com/quasi-drug-mall/{self.target_store_id}"
                else:
                    url = f"https://www.baropharm.com/brand/{self.target_store_id}"
                store_list = [{
                    "store_id": self.target_store_id,
                    "업체명": store_name,
                    "url": url,
                    "카테고리1": cat1,
                    "카테고리2": cat2,
                }]
            else:
                store_list = self.load_store_list_from_csv()

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
