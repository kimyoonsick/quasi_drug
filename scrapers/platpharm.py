import os
import time
import re
from .base import BaseScraper


class PlatpharmScraper(BaseScraper):
    name = "platpharm"

    BASE_URL = "https://www.platpharm.co.kr"
    VENDOR_ID = "S3160"

    def login(self):
        """사용자가 직접 로그인 + 팝업 처리. Enter로 수집 시작"""
        self.page.goto(self.BASE_URL, wait_until="domcontentloaded")
        time.sleep(2)

        # 아이디/비번 자동 입력 (로그인 버튼은 사용자가 클릭)
        user_id = os.getenv("platpharm_id")
        user_pw = os.getenv("platpharm_pw")
        email_input = self.page.query_selector('input[name="email"]')
        if email_input and user_id and user_pw:
            self.page.fill('input[name="email"]', user_id)
            self.page.fill('input[name="password"]', user_pw)
            print("아이디/비밀번호 자동 입력 완료")

        print(">> 로그인 + 팝업 닫기를 완료한 후 Enter를 눌러주세요...")
        input()
        time.sleep(1)

    def _build_url(self, category: str, page: int) -> str:
        from urllib.parse import quote
        return (
            f"{self.BASE_URL}/pharmacy/orders"
            f"?vendorId={self.VENDOR_ID}"
            f"&page={page}"
            f"&productCate={quote(category)}"
        )

    def _get_total_pages(self) -> int:
        """페이지네이션에서 총 페이지 수 추출 ("1 / 7" → 7)"""
        try:
            nav = self.page.query_selector("#product-list nav")
            if nav:
                text = nav.inner_text()
                m = re.search(r"/\s*(\d+)", text)
                if m:
                    return int(m.group(1))
        except Exception:
            pass
        return 1

    def _load_page(self, category: str, page_num: int) -> bool:
        """페이지 로딩 후 상품 존재 여부 반환. 정확히 1 요청"""
        url = self._build_url(category, page_num)
        print(f"  URL: {url}")
        self.page.goto(url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_selector('text=/\\d+원/', timeout=10000)
            return True
        except Exception:
            return False

    def scrape_category(self, category: str) -> list[dict]:
        results = []

        # 첫 페이지 로딩
        if not self._load_page(category, 1):
            print(f"  상품 없음, 건너뜀")
            return results

        time.sleep(1)
        total_pages = self._get_total_pages()
        print(f"  총 {total_pages}페이지")

        # 첫 페이지 수집
        items = self._extract_products(category)
        if items:
            results.extend(items)
            print(f"  페이지 1: {len(items)}건")

        # 나머지 페이지
        for page_num in range(2, total_pages + 1):
            self._delay()
            if not self._load_page(category, page_num):
                print(f"  페이지 {page_num}: 상품 없음, 수집 종료")
                break

            time.sleep(1)
            items = self._extract_products(category)
            if not items:
                print(f"  페이지 {page_num}: 파싱 실패, 수집 종료")
                break

            results.extend(items)
            print(f"  페이지 {page_num}: {len(items)}건")

        return results

    def _extract_products(self, category: str) -> list[dict]:
        """로드된 DOM에서 상품 정보 추출"""
        items = []

        # check-item-{코드}에서 상품코드 추출
        product_codes = _eval_safe(self.page, """() => {
            const codes = [];
            document.querySelectorAll('input[id^="check-item-"]').forEach(el => {
                codes.push(el.id.replace('check-item-', ''));
            });
            return codes;
        }""")

        # 텍스트 기반 상품 파싱 (첫 성공 실행과 동일 로직)
        body_text = self.page.inner_text("body")
        text_lines = [l.strip() for l in body_text.split("\n") if l.strip()]

        price_indices = []
        for i, line in enumerate(text_lines):
            if re.match(r"^[\d,]+원$", line):
                price_indices.append(i)

        for idx, pi in enumerate(price_indices):
            price = int(re.sub(r"[^\d]", "", text_lines[pi]))
            code = product_codes[idx] if idx < len(product_codes) else ""

            name = ""
            spec = ""
            skip = {"1", "+", "-", "품절"}

            for offset in range(1, min(6, pi + 1)):
                line = text_lines[pi - offset]
                if line in skip or len(line) <= 1:
                    continue
                if re.match(r"^[\d,]+원$", line):
                    break
                if any(kw in line for kw in ("추천순", "신상품순", "상품을 검색", "품절 제외")):
                    break

                if not spec:
                    spec = line
                elif not name:
                    name = line
                    break

            if name and price:
                items.append({
                    "상품코드": code,
                    "카테고리": category,
                    "상품명": name,
                    "규격": spec,
                    "가격": price,
                    "출처": self.name,
                })

        return items


def _eval_safe(page, script):
    try:
        return page.evaluate(script)
    except Exception:
        return []
