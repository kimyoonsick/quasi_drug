import os
import glob
import pandas as pd
from datetime import datetime

# 데이터가 위치한 최상위 디렉터리
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

TARGET_HEADERS = [
    "분류", "일반/특별", "제휴사", "프로모션명", "기한",
    "내용", "카테고리", "혜택", "Thumbnail", "Detail"
]

def process_all_csvs():
    # 데이터 디렉토리 확인
    if not os.path.exists(DATA_DIR):
        print(f"Data directory not found: {DATA_DIR}")
        return

    malls = ['hmpmall', 'saeropharm', 'baropharm', 'platpharm']
    total_processed_count = 0
    current_time = datetime.now().strftime("%y%m")
    
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
            
            # 'nan' 문자열 처리
            if title == 'nan': title = ''
            if duration == 'nan': duration = ''
            if benefit == 'nan': benefit = ''
            if thumbnail == 'nan': thumbnail = ''
            if detail == 'nan': detail = ''

            # 새 헤더 규격에 맞게 맵핑
            processed_row = {
                "분류": f"[{mall_name}] 미분류",  # 임시로 몰 이름과 빈 분류 넣음
                "일반/특별": "일반",            # 사용자가 수동 수정하기 전까지 일반으로 고정
                "제휴사": "",
                "프로모션명": title,
                "기한": duration,
                "내용": "",                    # Image Vision 전까지 비워둠
                "카테고리": "",                # Image Vision 전까지 비워둠
                "혜택": benefit,               # 기존에 스크래퍼가 가져온 텍스트가 있다면 일단 넣음
                "Thumbnail": thumbnail,
                "Detail": detail
            }
            mall_data.append(processed_row)
            
        # 개별 몰별 CSV 저장
        if mall_data:
            final_df = pd.DataFrame(mall_data, columns=TARGET_HEADERS)
            # 사용자가 변경을 요청한 파일명 규칙: yymm_경쟁사명
            output_filename = f"{current_time}_{mall}.csv"
            output_path = os.path.join(DATA_DIR, output_filename)
            
            final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"✅ [{mall}] Saved 10-header CSV to: {output_path} ({len(final_df)}건)")
            total_processed_count += len(final_df)

    if total_processed_count == 0:
        print("No event data found to process.")
        return

    print(f"\n✅ Processing Complete! Total {total_processed_count} events processed across various malls.")

if __name__ == "__main__":
    process_all_csvs()
