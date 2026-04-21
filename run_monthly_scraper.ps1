# run_monthly_scraper.ps1
# B2B 약국 사이트 이벤트 스크래핑 및 가공 자동화 스크립트
# 바탕화면에 바로가기를 만들거나 Windows 작업 스케줄러에 등록하기 좋습니다.

# UTF-8 출력 강제 적용 (이모지 텍스트 인코딩 에러 방지)
$env:PYTHONIOENCODING="utf-8"

Write-Host "==============================================="
Write-Host " 약국 B2B 메디컬 통합 이벤트 스크래핑 파이프라인 "
Write-Host "==============================================="

# uv run으로 전체 스크래핑 & 가공 로직(main.py) 돌리기
uv run main.py

Write-Host ""
Write-Host "모든 파이프라인이 정상적으로 종료되었습니다."
Write-Host "결과는 data/ 폴더 하위를 확인해 주세요."
Pause
