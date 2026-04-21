# uv 패키지 매니저 가이드

공식 문서: https://docs.astral.sh/uv/

## uv란

Rust로 작성된 초고속 Python 패키지/프로젝트 매니저
pip, venv, pyenv, poetry를 하나의 도구로 대체
pip 대비 10-100배 빠른 의존성 해석 속도

## 설치

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 확인:
```bash
uv --version
```

참고: https://docs.astral.sh/uv/getting-started/installation/

## 프로젝트 초기화

```bash
uv init
```

생성되는 파일:
- pyproject.toml: 프로젝트 메타데이터 및 의존성 선언
- .python-version: 사용할 Python 버전
- README.md
- main.py

참고: https://docs.astral.sh/uv/guides/projects/#creating-a-new-project

## 의존성 관리

### 패키지 추가
```bash
uv add pandas
uv add "numpy>=2.0"
uv add 'requests==2.31.0'
```

### Git 저장소에서 추가
```bash
uv add git+https://github.com/psf/requests
```

### requirements.txt에서 마이그레이션
```bash
uv add -r requirements.txt
```

### 패키지 제거
```bash
uv remove requests
```

### 패키지 업그레이드
```bash
uv lock --upgrade-package requests
```

### 개발 의존성 추가
```bash
uv add --dev pytest
uv add --dev ruff
```

참고: https://docs.astral.sh/uv/guides/projects/#managing-dependencies

## 스크립트 실행

```bash
uv run main.py
uv run scripts/scrape_platpharm.py
```

uv run은 실행 전에 자동으로:
1. uv.lock이 pyproject.toml과 동기화되었는지 확인
2. 가상환경이 lockfile과 일치하는지 확인
3. 필요시 자동으로 동기화 후 실행

별도의 venv activate 없이 바로 실행 가능

참고: https://docs.astral.sh/uv/guides/projects/#running-commands

## 환경 동기화

```bash
# lockfile 기준으로 가상환경 동기화 (클론 후 최초 설정 시)
uv sync

# 의존성 해석 및 lockfile 갱신
uv lock

# 의존성 트리 출력
uv tree
```

참고: https://docs.astral.sh/uv/concepts/projects/sync/

## Python 버전 관리

```bash
# Python 버전 설치
uv python install 3.14

# 현재 디렉토리에 Python 버전 고정
uv python pin 3.11

# 설치된 Python 버전 목록
uv python list
```

참고: https://docs.astral.sh/uv/guides/install-python/

## 핵심 명령어 레퍼런스

| 명령어 | 설명 |
|---|---|
| uv init | 새 프로젝트 초기화 |
| uv add <패키지> | 의존성 추가 |
| uv remove <패키지> | 의존성 제거 |
| uv run <명령> | 프로젝트 환경에서 명령 실행 |
| uv sync | 가상환경을 lockfile에 맞게 동기화 |
| uv lock | 의존성 해석 및 lockfile 갱신 |
| uv tree | 의존성 트리 출력 |
| uv python install <버전> | 특정 Python 버전 설치 |
| uv pip list | 설치된 패키지 목록 |
| uv lock --upgrade-package <패키지> | 특정 패키지 업그레이드 |

## 프로젝트 핵심 파일

| 파일 | 역할 |
|---|---|
| pyproject.toml | 프로젝트 메타데이터, 의존성 선언 |
| uv.lock | 모든 의존성의 정확한 잠금 버전 (Git 커밋 대상) |
| .python-version | 프로젝트 Python 버전 지정 |
| .venv/ | 가상환경 디렉토리 (.gitignore 대상) |

## 현재 프로젝트 (quasi_drug)

```
quasi_drug/
├── pyproject.toml              # Python 3.14, beautifulsoup4, pandas, playwright, python-dotenv, requests
├── uv.lock
├── .python-version             # 3.14
├── .venv/
├── scrapers/                   # 스크래핑 모듈 (base.py, platpharm.py)
├── scripts/                    # 분석 스크립트 (marketing_analysis.py 등)
├── data/                       # 데이터 폴더
└── output/                     # 출력 폴더
```

## 트러블슈팅

### 가상환경이 꼬였을 때
```bash
rmdir /s /q .venv
uv sync
```

### lockfile 충돌 시
```bash
uv lock
```

### 특정 Python 버전이 없을 때
```bash
uv python install 3.14
```

### 패키지 충돌 시
```bash
uv tree
uv lock --upgrade
```

### Playwright 브라우저 설치
```bash
uv run playwright install
```
