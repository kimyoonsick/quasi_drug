# scrapers/base.py
"""약국 쇼핑몰 이벤트 스크래퍼 베이스 클래스 (async)

봇 탐지 회피 원칙:
- stealth 브라우저 컨텍스트 (webdriver 숨김, 실제 UA)
- 이미지/폰트 허용 (정상 유저처럼), 분석 스크립트만 차단
- 자연스러운 마우스 이동, 스크롤 등 인간적 행동
- 페이지 간 충분한 랜덤 딜레이
"""
from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import pandas as pd
import os
import asyncio
import aiohttp
import random
import re

from .bot_helper import (
    create_stealth_context,
    human_delay,
    human_scroll,
    human_mouse_move,
    handle_bot_challenge,
    block_analytics_only,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class BaseEventScraper(ABC):
    """이벤트 스크래퍼 베이스 클래스 (async)"""

    name: str = ""
    # 사이트별 딜레이 (초) - 서브클래스에서 오버라이드
    delay_min: float = 8.0
    delay_max: float = 15.0

    def __init__(self):
        self.data: list[dict] = []
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._pw = None

    # ── 브라우저 관리 ────────────────────────────────────────

    async def start_browser(self, headless: bool = False):
        """stealth 브라우저 시작"""
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=headless)
        
        context_args = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "locale": "ko-KR",
            "timezone_id": "Asia/Seoul",
        }

        # 이전에 저장된 세션(쿠키 등)이 있다면 불러오기
        state_path = BASE_DIR / ".cookies" / f"{self.name}_state.json"
        if state_path.exists():
            context_args["storage_state"] = str(state_path)

        self.context = await create_stealth_context(self.browser, **context_args)
        self.page = await self.context.new_page()
        # 분석 스크립트만 차단 (이미지/폰트는 허용)
        await block_analytics_only(self.page)

    async def stop_browser(self):
        """브라우저 자원 반환 및 세션 저장"""
        # 현재 컨텍스트의 상태(쿠키, 스토리지)를 저장하여 로그인 유지
        if self.context:
            try:
                state_path = BASE_DIR / ".cookies" / f"{self.name}_state.json"
                await self.context.storage_state(path=str(state_path))
            except Exception as e:
                print(f"[base] 세션 저장 중 오류: {e}")

        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()

    # ── 딜레이 & 인간적 행동 ─────────────────────────────────

    async def _delay(self, min_sec: float | None = None, max_sec: float | None = None):
        """페이지 간 랜덤 딜레이 + 간헐적 마우스/스크롤"""
        _min = min_sec or self.delay_min
        _max = max_sec or self.delay_max

        # 간헐적으로 마우스 이동이나 스크롤 추가
        if random.random() < 0.3:
            await human_mouse_move(self.page)
        if random.random() < 0.2:
            await human_scroll(self.page)

        await human_delay(_min, _max)

    # ── 이미지 다운로드 ──────────────────────────────────────

    async def download_image(self, url: str, save_path: Path) -> bool:
        """이미지 URL에서 파일 다운로드

        Args:
            url: 이미지 URL
            save_path: 저장할 파일 경로

        Returns:
            성공 여부
        """
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            # 브라우저 쿠키를 사용하여 인증된 상태로 다운로드
            cookies = await self.context.cookies()
            cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Cookie": cookie_header,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
                    "Referer": self.page.url,
                }
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        save_path.write_bytes(content)
                        return True
                    else:
                        print(f"  [이미지] HTTP {resp.status}: {url[:80]}")
                        return False
        except Exception as e:
            print(f"  [이미지] 다운로드 실패: {e}")
            return False

    async def download_event_images(self, event: dict, image_urls: list[str]) -> list[str]:
        """이벤트의 이미지들을 다운로드하고 로컬 경로 목록 반환"""
        saved_paths = []
        event_dir = BASE_DIR / "data" / self.name / "events"
        event_dir.mkdir(parents=True, exist_ok=True)

        # 이벤트 제목에서 파일명 안전 문자열 생성
        safe_title = re.sub(r'[<>:"/\\|?*\n\r]', '_', event.get("event_title", "") or "")[:50].strip('_ ')

        # 타이틀이 없으면 URL에서 고유 식별자 추출
        if not safe_title:
            import hashlib
            url_hash = hashlib.md5(str(image_urls).encode()).hexdigest()[:8]
            safe_title = f"event_{url_hash}"

        for i, img_url in enumerate(image_urls):
            if not img_url:
                continue
            # 확장자 추출
            ext = ".jpg"
            for e in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                if e in img_url.lower():
                    ext = e
                    break

            # URL에서 고유 부분 추출 (이벤트 ID 등)
            url_id = ""
            id_match = re.search(r'/(\d{3,})[/_]', img_url)
            if id_match:
                url_id = f"_{id_match.group(1)}"

            filename = f"{safe_title}{url_id}_{i+1}{ext}"
            save_path = event_dir / filename

            if await self.download_image(img_url, save_path):
                saved_paths.append(str(save_path))
                print(f"  [이미지] 저장: {filename}")

            # 이미지 다운로드 간 짧은 딜레이
            await asyncio.sleep(random.uniform(0.5, 1.5))

        return saved_paths

    # ── 데이터 저장 ──────────────────────────────────────────

    def save(self, filename: str | None = None) -> Path | None:
        if not self.data:
            print("수집된 데이터가 없습니다")
            return None

        output_dir = BASE_DIR / "data" / self.name
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            from datetime import datetime
            filename = f"{self.name}_events_{datetime.now().strftime('%y%m%d_%H%M')}.csv"

        path = output_dir / filename
        df = pd.DataFrame(self.data)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"\n저장 완료: {path} ({len(df)}건)")
        return path

    def _save_incremental(self):
        """중간 저장 (중단 시 데이터 보존)"""
        if self.data:
            output_dir = BASE_DIR / "data" / self.name
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / f"{self.name}_events_진행중.csv"
            pd.DataFrame(self.data).to_csv(path, index=False, encoding="utf-8-sig")

    # ── 추상 메서드 ──────────────────────────────────────────

    @abstractmethod
    async def login(self):
        """사이트 로그인"""
        ...

    @abstractmethod
    async def extract_events(self) -> list[dict]:
        """이벤트 목록 수집"""
        ...

    # ── 실행 ─────────────────────────────────────────────────

    async def run(self, headless: bool = False) -> list[dict]:
        """스크래퍼 실행: 브라우저 시작 → 로그인 → 이벤트 수집 → 저장"""
        try:
            await self.start_browser(headless=headless)
            print(f"\n{'='*50}")
            print(f"[{self.name}] 스크래핑 시작")
            print(f"{'='*50}")

            # 로그인
            print(f"[{self.name}] 로그인 시도...")
            await self.login()
            print(f"[{self.name}] 로그인 완료")

            # 봇 챌린지 확인
            await handle_bot_challenge(self.page)

            # 딜레이 후 이벤트 수집
            await self._delay()

            print(f"[{self.name}] 이벤트 수집 시작...")
            events = await self.extract_events()
            self.data.extend(events)
            print(f"[{self.name}] 총 {len(events)}건 수집 완료")

            self.save()
            return self.data

        except Exception as e:
            print(f"[{self.name}] 오류 발생: {e}")
            self._save_incremental()
            raise
        finally:
            await self.stop_browser()
