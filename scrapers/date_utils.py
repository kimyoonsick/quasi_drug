# scrapers/date_utils.py
"""이벤트 날짜 파싱 및 만료 여부 판단 유틸리티"""
import re
from datetime import datetime, date


def parse_end_date(duration_str: str) -> date | None:
    """기간 문자열에서 종료일을 파싱하여 date 객체로 반환.

    지원 형식:
        2025.01.01 ~ 2025.12.31
        2025-01-01 ~ 2025-12-31
        2025/01/01 ~ 2025/12/31
        2025.01.01 ~ 12.31  (연도 생략)
        2025년 01월 01일 ~ 2025년 12월 31일
    """
    if not duration_str:
        return None

    # 전처리: 공백 통일, 구분자 정규화
    s = duration_str.strip()

    # 날짜 토큰 전체 추출 (숫자+구분자 패턴)
    tokens = re.findall(r'\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}년\s*\d{1,2}월\s*\d{1,2}일', s)

    if not tokens:
        return None

    def to_date(token: str, fallback_year: int | None = None) -> date | None:
        token = re.sub(r'[년월일\s]', '.', token).strip('.')
        token = re.sub(r'[/-]', '.', token)
        parts = [p for p in token.split('.') if p]
        if len(parts) == 3:
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if y < 100 and fallback_year:
                    y = fallback_year
                return date(y, m, d)
            except ValueError:
                pass
        elif len(parts) == 2 and fallback_year:
            try:
                m, d = int(parts[0]), int(parts[1])
                return date(fallback_year, m, d)
            except ValueError:
                pass
        return None

    # 종료일은 마지막 토큰
    end_token = tokens[-1]
    start_year = None
    if len(tokens) >= 2:
        first = to_date(tokens[0])
        if first:
            start_year = first.year

    return to_date(end_token, fallback_year=start_year)


def is_expired(duration_str: str, today: date | None = None) -> bool | None:
    """이벤트가 이미 종료되었는지 판단.

    Returns:
        True  - 이미 종료된 이벤트
        False - 아직 진행 중인 이벤트
        None  - 날짜를 파싱할 수 없어 판단 불가
    """
    if today is None:
        today = date.today()

    end_date = parse_end_date(duration_str)
    if end_date is None:
        return None
    return end_date < today
