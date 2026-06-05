# 단계별 빌드 프롬프트 (P0–P5)

Claude Code에 **한 번에 하나씩** 붙여넣어 실행한다. 각 프롬프트는 `CLAUDE.md`·`docs/`를 전제한다. 단계 완료 = `ROADMAP.md`의 exit criteria 충족 + 커밋.

> 모든 단계 공통 머리말(매번 포함 권장):
> "CLAUDE.md의 GOLDEN RULES와 docs/guidelines를 준수한다. 시작 전 이 단계의 목표·산출·완료기준을 한 문단으로 요약하고, 변경할 파일 목록을 제시한 뒤 구현→테스트→커밋한다. 한 단계만 진행한다."

---

## P0 — 부트스트랩
```
docs/PRD.md, SDD.md, TDD.md, CLAUDE.md를 읽고 레포 스캐폴드를 만들어줘.
- pyproject.toml (Python 3.12, deps: pydantic v2, pydantic-settings, pyyaml, jsonschema, pytest, ruff, mypy; FastAPI/uvicorn, streamlit는 extras)
- src/turtle_insight/ 패키지 골격(TDD §1 레이아웃의 빈 모듈 + __init__)
- config/settings.py (pydantic-settings, TDD §8의 env 키)
- Makefile (setup/lint/test/validate/run-api/run-viewer 타깃)
- .pre-commit-config.yaml (ruff, mypy), ruff/mypy 설정
- .github/workflows/ci.yml (R1 validate + R2 lint/test)
- tests/ 골격(빈 그린 테스트)
완료기준: make setup/lint/test 통과, CI 동작. 커밋.
```

## P1 — 도메인 코어
```
TDD §2–3, guidelines/thesis-and-epistemics.md를 기준으로 도메인 코어를 구현해줘.
- domain/thesis.py (Thesis/Evidence/AssetLink/Enums), signal.py, proposal.py(Proposal/Brief/Review)
- domain/state.py: ALLOWED_TRANSITIONS + can_promote_to_active() (게이트: falsifiers + dated evidence + RedTeam pass)
- domain/calibration.py: 예측 등록·채점 골격
- services/validation.py (=R1): schema/thesis.schema.yaml로 theses/ 검증 + 고아 링크 검사
- 단위테스트: 상태전이(양/음성), 승격 게이트, 스키마 검증. theses/examples가 검증 통과해야 함.
완료기준: 게이트/전이 테스트 통과, make validate 그린. 커밋.
```

## P2 — 저장 + 동기화
```
TDD §4를 구현해줘.
- storage/files.py: theses/<status>/<id>.yaml 읽기/쓰기, 상태변경 시 폴더 이동
- storage/sql_models.py(SQLAlchemy), sqlite_repo.py(ThesisRepository/SignalRepository 구현), repository.py(인터페이스)
- make sync: files → db 단방향 동기화. CI에 files↔db 불일치 검사 추가
- 통합테스트: 예시 테제 파일↔DB 왕복, 상태 이동 시 폴더 이동
완료기준: 동기화·왕복 테스트 통과. 커밋.
```

## P3 — 수집 + 추론 게이트
```
SDD §4–5, TDD §5를 구현해줘.
- connectors/base.py(Connector 인터페이스) + MVP 커넥터: edgar, dart, fred, market_api(yfinance), news. 모두 녹화 픽스처 기반(라이브 호출 금지). 뉴스는 링크+≤500자 요약만.
- services/inference.py: deep(Claude, TI_DEEP_MODEL)/fast(로컬 or deep 폴백) 게이트, prompt_version·토큰 로깅. 모델명 하드코딩 금지.
- agents/base.py(Agent 계약) + agents/scout.py: 픽스처에서 시그널 적재·정규화·태깅
- 테스트: Scout가 픽스처로 시그널 생성(전문 미저장), inference는 목으로
완료기준: Scout 통합테스트 통과. 커밋.
```

## P4 — 분석 + 게이트 (씨앗 테제 active까지)
```
AGENTS.md, guidelines를 기준으로 분석 1주기를 구현해줘.
- agents/analyst.py: 시그널→Asset/Chain 테제(candidate) 생성, 근거에 signal 링크, falsifiers 명시
- agents/redteam.py: 베어 케이스·반증조건 점검·편향 플래그 → Review(verdict)
- services/orchestrator.py: Scout→Analyst→RedTeam 1주기, candidate→(pass)→active
- evals/: active 후보에 falsifiers·dated evidence 존재, 출력에 전문 인용 없음 검사
- 씨앗 테제(theses/examples 계열)가 게이트를 통과해 active가 되도록
완료기준: 씨앗 테제 active, eval 통과. 커밋.
```

## P5 — 제안 + 전달 + 뷰어 (MVP 완성)
```
AGENTS.md, SDD §6를 구현해 MVP를 완성해줘.
- agents/allocator.py: active 테제 + 제약(위험성향·시계·제외)으로 Proposal 생성. 강세/기본/약세 시나리오 + 사이징 논리 + 리스크. 명령형 단정 금지.
- agents/synthesizer.py: 위클리 브리핑(Markdown). 링크+요약만 사용.
- agents/curator.py: 예측 등록·캘리브레이션 채점·아카이브·근거 신선도 플래그
- api/app.py(FastAPI 조회 엔드포인트, TDD §6 — 매매 엔드포인트 없음), viewer/app.py(Streamlit: 그래프·테제 상세·제안·브리핑)
- eval: Allocator 출력이 시나리오/리스크 포함(GOLDEN RULE 2)
완료기준: 위클리 브리핑·제안 자동 생성, 뷰어에서 테제 그래프 탐색. PRD §8 성공기준 충족. 커밋.
```

---

이후 단계(Macro/Strategist/Market, Postgres+pgvector, Dramatiq/launchd, 로컬 모델, 브리핑 확장)는 `ROADMAP.md §이후`를 새 프롬프트로 작성해 진행한다.
