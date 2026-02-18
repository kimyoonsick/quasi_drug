# uv 프로젝트 지침서

이 프로젝트는 Python 패키지 및 프로젝트 관리를 위해 **[uv](https://docs.astral.sh/uv/)** 를 사용합니다.

## uv란?

`uv`는 Rust로 작성된 초고속 Python 패키지 및 프로젝트 매니저입니다.  
기존의 `pip`, `venv`, `pyenv`, `poetry` 등을 **하나의 도구로 대체**할 수 있습니다.

- 📖 공식 문서: https://docs.astral.sh/uv/
- 📦 GitHub: https://github.com/astral-sh/uv

---

## 빠른 시작

### 1. uv 설치

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> 📖 설치 가이드: https://docs.astral.sh/uv/getting-started/installation/

### 2. 프로젝트 초기화

```bash
uv init
```

- `pyproject.toml`, `.python-version`, `README.md`, `main.py` 파일이 자동 생성됩니다.
- 이미 `pyproject.toml`이 존재하면 에러가 발생합니다.

> 📖 참고: https://docs.astral.sh/uv/guides/projects/#creating-a-new-project

### 3. 의존성(패키지) 추가

```bash
uv add 패키지명
```

예시:
```bash
uv add pandas          # pandas 설치
uv add requests        # requests 설치
uv add "numpy>=2.0"    # 버전 지정 설치
```

- 가상환경(`.venv`)이 없으면 자동으로 생성합니다.
- `pyproject.toml`의 `[project.dependencies]`에 자동 추가됩니다.
- `uv.lock` 파일이 생성/갱신되어 정확한 버전이 잠깁니다.

> 📖 참고: https://docs.astral.sh/uv/guides/projects/#managing-dependencies

### 4. 파일 실행

```bash
uv run 파일명.py
```

예시:
```bash
uv run analyze_pharmacy.py
uv run main.py
```

- 실행 전 자동으로 `uv.lock`과 가상환경을 동기화합니다.
- **별도의 `venv activate` 없이** 바로 실행할 수 있습니다.

> 📖 참고: https://docs.astral.sh/uv/guides/projects/#running-commands

---

## 주요 명령어 레퍼런스

| 명령어 | 설명 | 공식 문서 |
|---|---|---|
| `uv init` | 새 프로젝트 초기화 | [Creating projects](https://docs.astral.sh/uv/guides/projects/#creating-a-new-project) |
| `uv add <패키지>` | 의존성 추가 | [Managing dependencies](https://docs.astral.sh/uv/guides/projects/#managing-dependencies) |
| `uv remove <패키지>` | 의존성 제거 | [Managing dependencies](https://docs.astral.sh/uv/guides/projects/#managing-dependencies) |
| `uv run <명령>` | 프로젝트 환경에서 명령 실행 | [Running commands](https://docs.astral.sh/uv/guides/projects/#running-commands) |
| `uv sync` | 가상환경을 lockfile에 맞게 동기화 | [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) |
| `uv lock` | 의존성 해석 및 lockfile 갱신 | [Locking](https://docs.astral.sh/uv/concepts/projects/lock/) |
| `uv tree` | 의존성 트리 출력 | [Dependency tree](https://docs.astral.sh/uv/reference/cli/#uv-tree) |
| `uv python install <버전>` | 특정 Python 버전 설치 | [Python versions](https://docs.astral.sh/uv/guides/install-python/) |
| `uv pip list` | 설치된 패키지 목록 확인 | [pip interface](https://docs.astral.sh/uv/pip/packages/) |

---

## 개발 의존성 관리

테스트, 린트 등 개발 전용 패키지는 `--dev` 플래그를 사용합니다:

```bash
uv add --dev pytest     # 테스트 프레임워크
uv add --dev ruff       # 린트/포매터
```

> 📖 참고: https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies

---

## 프로젝트 구조

```
partial_return_point/
├── data/                          # 데이터 파일
│   └── prpoint_230105_260205.CSV
├── .venv/                         # 가상환경 (자동 생성, Git 제외)
├── pyproject.toml                 # 프로젝트 설정 및 의존성
├── uv.lock                        # 의존성 잠금 파일
├── .python-version                # Python 버전 지정
├── analyze_pharmacy.py            # 사업자번호 기준 약국 분석 스크립트
├── UV_GUIDE.md                    # 이 문서
└── README.md
```

---

## 핵심 파일 설명

| 파일 | 설명 |
|---|---|
| `pyproject.toml` | 프로젝트 메타데이터, 의존성 선언, 빌드 설정 |
| `uv.lock` | 모든 의존성의 정확한 버전이 잠긴 파일. **반드시 Git에 커밋**하세요. |
| `.python-version` | 프로젝트에서 사용할 Python 버전 |
| `.venv/` | 가상환경 디렉토리. `.gitignore`에 포함되어 Git 추적에서 제외됩니다. |

---

## 자주 묻는 질문

### Q: `pip install` 대신 뭘 쓰나요?
**A:** `uv add <패키지>` 를 사용하세요. pyproject.toml과 lockfile이 자동으로 관리됩니다.

### Q: 가상환경을 직접 활성화해야 하나요?
**A:** `uv run`을 사용하면 **자동으로 가상환경 내에서 실행**되므로, 별도의 활성화가 필요 없습니다.

### Q: 다른 사람의 프로젝트를 클론한 후 설정하려면?
**A:** 프로젝트 루트에서 `uv sync`를 실행하면 lockfile 기준으로 모든 의존성이 자동 설치됩니다.

### Q: Python 버전을 변경하려면?
**A:** `uv python install <버전>` (예: `uv python install 3.12`) 로 설치 후, `.python-version` 파일을 수정하세요.
