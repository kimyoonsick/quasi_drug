# scripts/merge_raw.py
"""Collect event data from all scrapers and store it in a CSV file with
custom Korean headers as defined by the user.

Headers (tab‑separated in the CSV):
분류\t일반/특별\t제휴사\t프로모션명\t기 한\t내 용\t혜 택\t비고
"""
import csv
import sys, os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure the project root is in PYTHONPATH for scraper imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from pathlib import Path

# Import scrapers (they expose a .run() coroutine returning a list of dicts)
from scrapers.hmp_scraper import HmpScraper
from scrapers.baropharm_scraper import BaropharmScraper
from scrapers.saeropharm_scraper import SaeropharmScraper
from scrapers.platpharm_scraper import PlatpharmScraper

# Output CSV path
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "competitor_raw.csv"

# ---------------------------------------------------------------------------
# Helper: map raw scraper dict to the user‑defined header structure
# ---------------------------------------------------------------------------
def map_to_custom_header(raw: dict) -> dict:
    """Convert a raw event dict to the custom Korean header format.

    The original dict contains keys:
        mall_name, event_title, benefit_summary, duration, target, detail_url
    The target format expects:
        분류, 일반/특별, 제휴사, 프로모션명, 기 한, 내 용, 혜 택, 비고
    """
    # 1️⃣ 분류: default to "자체" (user can edit later if needed)
    classification = "자체"
    # 2️⃣ 일반/특별: simple heuristic – if benefit contains large discount or the word "특별"
    benefit = raw.get("benefit_summary", "")
    if any(tok in benefit for tok in ["특별", "%", "할인", "리베이트"]):
        special = "특별"
    else:
        special = "일반"
    # 3️⃣ 제휴사: blank for 자체, otherwise mall_name (future use)
    partner = "" if classification == "자체" else raw.get("mall_name", "")
    # 4️⃣ 프로모션명: event_title
    promo_name = raw.get("event_title", "")
    # 5️⃣ 기 한: duration
    period = raw.get("duration", "")
    # 6️⃣ 내 용: benefit_summary
    content = benefit
    # 7️⃣ 혜 택: target (예: 신규, 전체 등)
    benefit_target = raw.get("target", "")
    # 8️⃣ 비고: we can store the detail URL for reference
    remarks = raw.get("detail_url", "")

    return {
        "분류": classification,
        "일반/특별": special,
        "제휴사": partner,
        "프로모션명": promo_name,
        "기 한": period,
        "내 용": content,
        "혜 택": benefit_target,
        "비고": remarks,
    }

# ---------------------------------------------------------------------------
async def gather_all() -> list[dict]:
    scrapers = [
        HmpScraper(),
        BaropharmScraper(),
        SaeropharmScraper(),
        PlatpharmScraper(),
    ]
    all_events = []
    for scraper in scrapers:
        try:
            # 타임아웃을 15초 -> 120초로 연장: 사용자가 콘솔에서 봇 챌린지 번호를 직접 입력할 수 있는 충분한 시간 확보
            raw_events = await asyncio.wait_for(scraper.run(), timeout=120.0)
            for ev in raw_events:
                all_events.append(map_to_custom_header(ev))
        except asyncio.TimeoutError:
            print(f"[{scraper.__class__.__name__}] error during run: Timeout (120s)")
        except Exception as e:
            print(f"[{scraper.__class__.__name__}] error during run: {e}")
    return all_events

def write_csv(rows: list[dict]):
    # Define the exact order of columns as required
    fieldnames = ["분류", "일반/특별", "제휴사", "프로모션명", "기 한", "내 용", "혜 택", "비고"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    events = asyncio.run(gather_all())
    write_csv(events)
    print(f"✅ {len(events)} records written to {OUTPUT}")
