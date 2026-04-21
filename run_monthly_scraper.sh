#!/usr/bin/env bash
# run_monthly_scraper.sh
# B2B 약국 사이트 이벤트 스크래핑 및 가공 자동화 스크립트
# Git Bash 또는 WSL 터미널에서 실행하세요.

export PYTHONIOENCODING="utf-8"
export PYTHONUTF8=1

echo "==============================================="
echo " 약국 B2B 메디컬 통합 이벤트 스크래핑 파이프라인 "
echo "==============================================="

uv run main.py

echo ""
echo "모든 파이프라인이 정상적으로 종료되었습니다."
echo "결과는 data/ 폴더 하위를 확인해 주세요."
