from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import pandas as pd
import os
import time
import random

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class BaseScraper(ABC):
    """약국 쇼핑몰 스크래퍼 베이스 클래스

    요청 최소화 원칙:
    - 페이지 이동만이 서버 요청 (1 URL = 1 요청)
    - DOM 조회(query_selector, evaluate)는 로컬 작업 → 추가 요청 없음
    - 이미지/폰트/분석 스크립트 전부 차단
    - 페이지 간 5~8초 랜덤 딜레이
    """

    name: str = ""
    delay_min: float = 5.0
    delay_max: float = 8.0

    def __init__(self):
        self.data: list[dict] = []
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None

    def start_browser(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

        # 불필요한 리소스 전부 차단 (서버 요청 최소화)
        self.page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}", lambda r: r.abort())
        self.page.route("*clarity.ms*", lambda r: r.abort())
        self.page.route("*microsoft.com/clarity*", lambda r: r.abort())
        self.page.route("*channel.io*", lambda r: r.abort())
        self.page.route("*googletagmanager.com*", lambda r: r.abort())
        self.page.route("*google-analytics.com*", lambda r: r.abort())
        self.page.route("*hotjar.com*", lambda r: r.abort())
        self.page.route("*fullstory.com*", lambda r: r.abort())

    def stop_browser(self):
        if self.browser:
            self.browser.close()
        if self._pw:
            self._pw.stop()

    def _delay(self):
        wait = random.uniform(self.delay_min, self.delay_max)
        time.sleep(wait)

    @abstractmethod
    def login(self):
        ...

    @abstractmethod
    def scrape_category(self, category: str) -> list[dict]:
        ...

    def save(self, filename: str | None = None):
        if not self.data:
            print("수집된 데이터가 없습니다")
            return

        output_dir = BASE_DIR / "data" / self.name
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            from datetime import datetime
            filename = f"{self.name}_{datetime.now().strftime('%y%m%d')}.csv"

        path = output_dir / filename
        df = pd.DataFrame(self.data)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"\n저장 완료: {path} ({len(df)}건)")
        return path

    def _save_incremental(self):
        """카테고리 수집 후 중간 저장 (중단 시 데이터 보존)"""
        if self.data:
            output_dir = BASE_DIR / "data" / self.name
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / f"{self.name}_진행중.csv"
            pd.DataFrame(self.data).to_csv(path, index=False, encoding="utf-8-sig")

    def run(self, categories: list[str]):
        try:
            self.start_browser()
            self.login()

            for i, cat in enumerate(categories):
                print(f"\n[{i+1}/{len(categories)}] [{cat}] 수집 시작")
                results = self.scrape_category(cat)
                self.data.extend(results)
                print(f"[{cat}] {len(results)}건 수집 완료")
                self._save_incremental()

                # 카테고리 간 딜레이
                if i < len(categories) - 1:
                    self._delay()

            self.save()
        finally:
            self.stop_browser()
