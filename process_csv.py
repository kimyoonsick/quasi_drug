import os
import glob
import pandas as pd
from datetime import datetime
import sqlite3
import re
import calendar

# 데이터가 위치한 최상위 디렉터리
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

TARGET_HEADERS = [
    "분류", "일반/특별", "제휴사", "프로모션명", "시작일", "종료일",
    "내용", "혜택", "카테고리", "Thumbnail", "Detail", "URL"
]

def process_all_csvs():
    # 데이터 디렉토리 확인
    if not os.path.exists(DATA_DIR):
        print(f"Data directory not found: {DATA_DIR}")
        return

    malls = ['hmp', 'saeropharm', 'baropharm', 'platpharm']
    total_processed_count = 0
    current_time = datetime.now().strftime("%y%m")
    
    # DB에서 제약사, 입점업체 목록 가져오기
    partner_names = set()
    db_path = os.path.join(BASE_DIR, "db", "picosales.db")
    if os.path.exists(db_path):
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT seller_name FROM sellers")
                for row in cursor.fetchall():
                    if row[0]: partner_names.add(row[0].strip())
                cursor.execute("SELECT manufacturer_name FROM manufacturers")
                for row in cursor.fetchall():
                    if row[0]: partner_names.add(row[0].strip())
        except Exception as e:
            print(f"Failed to read from picosales.db: {e}")

    # 두 글자 이상인 이름만 필터링 (너무 짧으면 오탐 가능)
    partner_names = {name for name in partner_names if len(name) >= 2}
    # 긴 이름이 먼저 매칭되도록 길이 역순 정렬 (예: 보고신약이 보고보다 먼저 매칭되게)
    partner_names_sorted = sorted(list(partner_names), key=len, reverse=True)

    for mall in malls:
        mall_dir = os.path.join(DATA_DIR, mall)
        if not os.path.isdir(mall_dir):
            continue
            
        mall_data = []
        # 이번에는 가장 최근에 생성된 csv 파일 하나만 가져옵니다 (최신 스크래핑 결과)
        csv_files = glob.glob(os.path.join(mall_dir, "*.csv"))
        if not csv_files:
            continue
            
        latest_csv = max(csv_files, key=os.path.getctime)
        print(f"[{mall}] Loading latest file: {os.path.basename(latest_csv)}")
        
        try:
            df = pd.read_csv(latest_csv, encoding='utf-8-sig')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(latest_csv, encoding='cp949')
            except Exception as e:
                print(f"Failed to read {latest_csv}: {e}")
                continue
                
        for _, row in df.iterrows():
            # 안전하게 기존 CSV 필드를 가져오기 (컬럼명이 다를 수 있음을 감안)
            mall_name = str(row.get('mall_name', mall))
            title = str(row.get('event_title', ''))
            duration = str(row.get('duration', ''))
            benefit = str(row.get('benefit_summary', ''))
            thumbnail = str(row.get('thumbnail_url', ''))
            detail = str(row.get('detail_images', ''))
            detail_url = str(row.get('detail_url', ''))
            
            # 'nan' 문자열 처리
            if title == 'nan': title = ''
            title = title.replace(' 이미지', '')
            if duration == 'nan': duration = ''
            if benefit == 'nan': benefit = ''
            if thumbnail == 'nan': thumbnail = ''
            if detail == 'nan': detail = ''
            if detail_url == 'nan': detail_url = ''

            # 새 헤더 규격에 맞게 맵핑
            category = "미분류"
            partner = ""
            for name in partner_names_sorted:
                if name in title:
                    # '위고'가 제품명인 '위고비' 안에서 매칭되는 오탐 방지
                    if name == "위고" and "위고비" in title:
                        continue
                    # '상시'가 제휴사로 오인되는 오탐 방지
                    if name == "상시":
                        continue
                    category = "제휴"
                    partner = name
                    break

            # 금융/결제/멤버십 제휴사 하드코딩 체크 (카드사, 페이 등)
            payment_partners = [
                "토스페이먼츠", "토스페이", "네이버페이", "카카오페이", "스마일페이", "페이코",
                "KB국민카드", "국민카드", "KB Pay", "NH농협카드", "농협카드",
                "신한카드", "삼성카드", "현대카드", "롯데카드", "우리카드", "하나카드", 
                "비씨카드", "BC카드", "경남은행", "BNK", "CJONE"
            ]
            for pp in payment_partners:
                # 대소문자 구분 없이 매칭 (KB Pay 등)
                if pp.lower() in title.lower():
                    category = "제휴"
                    partner = pp
                    break

            # 기한(duration)을 시작일과 종료일로 분리
            start_date = ""
            end_date = ""
            if duration:
                parts = duration.split('~')
                if len(parts) >= 2:
                    start_date = parts[0].strip()
                    end_date = parts[1].strip()
                else:
                    start_date = duration.strip()

            item_category = ""
            if "의약외품" in title or "더나은" in title:
                item_category = "의약외품"
                # 만약 타이틀에 [더나은]처럼 명시되어 있으면 의약외품 할당 후 해당 텍스트 제거
                if "[더나은]" in title:
                    title = title.replace("[더나은]", "").strip()

            if item_category and f"[{item_category}]" in title:
                title = title.replace(f"[{item_category}]", "").strip()

            if mall == 'hmp':
                # 자체 카테고리 체크 (미리 세팅된 partner 확인 가능성)
                if partner == "한미" or "한미" in title:
                    category = "자체"

                # 다양한 형태의 날짜 추출 (YY년 M월 OR YYYY.MM)
                date_match1 = re.search(r'(\d+)\s*년\s*(\d+)\s*월', title)
                date_match2 = re.search(r'(\d{4})\.(\d{2})', title)
                
                year_num, month_num = None, None
                match_str = ""
                
                if date_match1:
                    year_num = int(date_match1.group(1))
                    month_num = int(date_match1.group(2))
                    if year_num < 100: year_num += 2000
                    match_str = date_match1.group(0)
                elif date_match2:
                    year_num = int(date_match2.group(1))
                    month_num = int(date_match2.group(2))
                    match_str = date_match2.group(0)

                if year_num and month_num:
                    if not start_date: # 기존 duration 파싱된게 없으면 덮어쓰기
                        start_date = f"{year_num}-{month_num:02d}-01"
                        last_day = calendar.monthrange(year_num, month_num)[1]
                        end_date = f"{year_num}-{month_num:02d}-{last_day}"
                    
                    # 프로모션명에서 날짜 부분 완전 제거
                    title = title.replace(match_str, "").strip()

                if "월간이벤트" in title:
                    # 제휴사 추출: 월간이벤트 바로 뒤
                    after_event = title.split("월간이벤트")[1].strip()
                    if after_event:
                        possible_partner = after_event.split('(')[0].strip()
                        if possible_partner:
                            partner = possible_partner
                            if partner == "한미" or "한미" in partner:
                                category = "자체"
                            else:
                                category = "제휴"

                # 다중 공백 단일 공백으로 치환
                title = re.sub(r'\s+', ' ', title).strip()

            if mall == 'saeropharm' and "새로팜" in title:
                category = "자체"
            elif mall == 'platpharm' and "플랫팜" in title:
                category = "자체"

            # 제휴사가 분명히 파악된 경우 (ex: 신용카드사, 결제사 등), 자체를 덮어쓰고 '제휴'로 확정 
            # (단, hmp-한미는 자사몰 성격이므로 예외 유지)
            if partner and partner != "한미":
                category = "제휴"

            # 필렌즈 관련 타이틀인지 체크 (바로팜 전용 앱)
            if mall == 'baropharm' and "필렌즈" in title:
                category = "자체"
                partner = "필렌즈"

            # 바로팜의 경우 혜택 컬럼 데이터를 내용 컬럼으로 이동 및 분류/제휴사 매핑
            content_val = ""
            if mall == 'baropharm' and benefit:
                content_val = benefit
                benefit = ""
                if "팜올플러스 이벤트" in content_val:
                    category = "자체"
                    partner = "팜올플러스"
                elif "입점업체 이벤트" in content_val or "브랜드관 이벤트" in content_val:
                    category = "제휴"
                elif "바로팜 이벤트" in content_val:
                    category = "자체"

            # 시작일, 종료일 기반 1년(365일) 이상 이벤트는 타사 제휴가 아닌 경우 자체 프로모션으로 전환
            if start_date and end_date:
                try:
                    s_val = start_date.strip().replace('. ', '-').replace('.', '-')
                    e_val = end_date.strip().replace('. ', '-').replace('.', '-')
                    s_date = datetime.strptime(s_val[:10], "%Y-%m-%d")
                    e_date = datetime.strptime(e_val[:10], "%Y-%m-%d")
                    if (e_date - s_date).days > 365:
                        if not partner or partner == "한미":
                            category = "자체"
                except Exception:
                    pass

            processed_row = {
                "분류": category,  # 임시로 빈 분류 넣음
                "일반/특별": "일반",            # 사용자가 수동 수정하기 전까지 일반으로 고정
                "제휴사": partner,
                "프로모션명": title.strip(),
                "시작일": start_date,
                "종료일": end_date,
                "내용": content_val,                    # 바로팜 제외하고 Image Vision 전까지 비워둠
                "혜택": benefit,               # 기존에 스크래퍼가 가져온 텍스트가 있다면 일단 넣음
                "카테고리": item_category,                # Image Vision 전까지 비워둠
                "Thumbnail": thumbnail,
                "Detail": detail,
                "URL": detail_url
            }
            
            # 수집 대상 월(current_time 기준) 1일보다 이전에 종료된 과거 이벤트 스킵
            valid_event = True
            if end_date:
                try:
                    e_val = end_date.strip().replace('. ', '-').replace('.', '-')
                    e_date_check = datetime.strptime(e_val[:10], "%Y-%m-%d")
                    curr_y = int("20" + current_time[:2])
                    curr_m = int(current_time[2:4])
                    first_day_of_month = datetime(curr_y, curr_m, 1)
                    if e_date_check < first_day_of_month:
                        valid_event = False
                    elif e_date_check.year >= 2100:
                        valid_event = False
                except Exception:
                    pass
            
            if valid_event:
                mall_data.append(processed_row)
            
        # 개별 몰별 CSV 저장
        if mall_data:
            final_df = pd.DataFrame(mall_data, columns=TARGET_HEADERS)
            
            # 정렬 로직: 분류가 '자체'인 것 최상단 (팜올플러스는 그 아래), 그다음 기간이 짧은 순
            def get_sort_keys(row):
                if row.get('분류') == '자체':
                    is_own = 1 if row.get('제휴사') in ['팜올플러스', '필렌즈'] else 0
                else:
                    is_own = 2
                
                duration_days = 999999
                try:
                    s_val, e_val = str(row.get('시작일', '')).strip().replace('.', '-'), str(row.get('종료일', '')).strip().replace('.', '-')
                    if s_val and e_val and s_val != 'nan' and e_val != 'nan':
                        # 날짜 파싱 (기본적인 YYYY-MM-DD 대응)
                        s = datetime.strptime(s_val[:10], "%Y-%m-%d")
                        e = datetime.strptime(e_val[:10], "%Y-%m-%d")
                        duration_days = (e - s).days
                except Exception:
                    pass
                return pd.Series([is_own, duration_days])

            if len(final_df) > 0:
                final_df[['_sort_own', '_sort_dur']] = final_df.apply(get_sort_keys, axis=1)
                final_df = final_df.sort_values(by=['_sort_own', '_sort_dur']).drop(columns=['_sort_own', '_sort_dur'])

            # 사용자가 변경을 요청한 파일명 규칙: yymm_경쟁사명
            output_filename = f"{current_time}_{mall}.csv"
            output_path = os.path.join(DATA_DIR, output_filename)
            
            final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"[SUCCESS] [{mall}] Saved 10-header CSV to: {output_path} ({len(final_df)}건)")
            total_processed_count += len(final_df)

    if total_processed_count == 0:
        print("No event data found to process.")
        return

    print(f"\n[SUCCESS] Processing Complete! Total {total_processed_count} events processed across various malls.")

if __name__ == "__main__":
    process_all_csvs()
