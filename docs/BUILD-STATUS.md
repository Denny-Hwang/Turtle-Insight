# BUILD STATUS
auto-build 가 이 파일로 진행 상태를 추적/재개한다.

| 단계 | 완료 | 머지 | 결과 한 줄 |
|---|---|---|---|
| P0 부트스트랩 | [x] | [x] | 레포 스캐폴드(uv/py3.12, src 41모듈, ruff+mypy, CI R1/R2) — PR #2, CI green |
| P1 도메인 코어 | [x] | [x] | domain 모델/상태기계/캘리브레이션 + R1 검증, 단위테스트 그린, examples 검증 통과 |
| P2 저장+동기화 | [x] | [x] | files 정본/상태이동 + SQLAlchemy sqlite_repo + make sync(+CI sync-check), 왕복 통합테스트 그린 |
| P3 수집+추론 게이트 | [x] | [x] | 픽스처 커넥터(edgar/dart/fred/market_api/news) + inference deep/fast 게이트 + Scout, 통합/목 테스트 그린 |
| P4 분석+게이트(씨앗 테제 active) | [x] | [x] | Analyst(시그널→candidate)+RedTeam(verdict)+Orchestrator 1주기, 씨앗 T-2026-0100 active, eval 그린 |
| P5 제안+전달+뷰어(MVP) | [x] | [x] | Allocator/Synthesizer/Curator + FastAPI 조회 + Streamlit 뷰어, 제안·브리핑 자동생성, eval 그린 — MVP 완성 |

## v1.x (MVP 이후)

| 단계 | 완료 | 머지 | 결과 한 줄 |
|---|---|---|---|
| P6 Macro/Strategist/Market | [x] | [x] | 공용 templates + Macro(0001)/Strategist(0002)/Market(regime), run_full_cycle로 macro→trend→chain 3계층 active, eval 그린 |

## 사전점검 — 현재 상태 판단 (2026-06-05)
- 레포 종합: `src/turtle_insight/` 41개 모듈 존재하나 `domain/`·`storage/`·`agents/`·`connectors/`·`services/`는 전부 docstring 스텁("Implemented in P*"). 실로직은 `config/settings.py`(+`services/validation.py` R1 스텁)뿐.
- tests: `unit/test_smoke.py` + integration/evals 플레이스홀더만. `theses/`는 `examples/`만(상태 폴더 없음).
- git/CI: P0가 PR #2로 main 머지, CI(R1/R2) green(run #3 success).
- 판단: **P0 완료·머지됨. P1–P5 미시작.** → 다음 시작 단계 = **P1 도메인 코어**.

## 단계별 계획·메모

### P1 도메인 코어 (TDD §2–3, thesis-and-epistemics.md)
- 목표: 테제 그래프 도메인 코어와 R1 검증을 구현. 게이트/전이를 1급 테스트로 강제.
- 산출: `domain/thesis.py`(Thesis/Evidence/AssetLink/Enums), `signal.py`, `proposal.py`(Review/Proposal/Brief/Constraints), `state.py`(ALLOWED_TRANSITIONS+can_promote_to_active+promote), `calibration.py`(Prediction/Outcome/score). `services/validation.py`(R1: 스키마+고아링크+active근거 불변식).
- 변경파일: 위 5개 domain 모듈 + validation.py + `tests/unit/test_{domain,state,calibration,validation}.py`.
- 완료기준: 게이트·전이 테스트 통과, `make validate` 그린(theses/examples 통과). examples는 schema 검증, 고아링크는 canonical 한정(examples 제외).

### P2 저장+동기화 (TDD §4, ADR-0006)
- 목표: 파일 정본↔DB 인덱스. 상태 변경 시 폴더 이동, files→db 단방향 동기화.
- 산출: `storage/files.py`(theses/<status>/<id>.yaml r/w + 상태이동), `sql_models.py`(SQLAlchemy), `repository.py`(인터페이스), `sqlite_repo.py`(구현), `storage/sync.py`(`make sync`/`--check`). dep: `sqlalchemy>=2.0`.
- 변경파일: 위 storage 모듈 + Makefile(sync/sync-check) + ci.yml(sync-check) + ADR-0006 + `tests/integration/test_storage.py`.
- 완료기준: 파일↔DB 왕복·상태이동·동기화 통합테스트 통과. MVP DB는 무손실(JSON parents/children/falsifiers/risks + assets/evidence 테이블).

### P3 수집+추론 게이트 (SDD §4–5, TDD §5)
- 목표: 라이브 호출 없는 픽스처 커넥터, 단일 추론 게이트(deep/fast), Scout 시그널 적재.
- 산출: `connectors/base.py`(Connector+FixtureConnector+fixtures/*.json) + edgar/dart/fred/market_api/news, `services/inference.py`(deep/fast, prompt_version·토큰 로깅, 모델명 config), `agents/base.py`(Agent/AgentContext/AgentResult), `agents/scout.py`(정규화+태깅+upsert).
- 변경파일: 위 모듈 + 5개 fixture JSON + `tests/unit/test_inference.py` + `tests/integration/test_scout.py`.
- 완료기준: Scout 통합테스트(픽스처→시그널, 링크+요약, 멱등), inference 목 테스트 통과. 라이브 호출 0, 전문 미저장.

### P4 분석+게이트 (AGENTS.md, guidelines)
- 목표: Scout→Analyst→RedTeam 1주기로 씨앗 테제를 candidate→active까지. 게이트 강제.
- 산출: `agents/analyst.py`(시그널→candidate, evidence에 signal_id 링크, falsifiers 명시; 결정적 룰베이스), `agents/redteam.py`(bear case·반증/근거 점검·편향 플래그→Review verdict), `services/orchestrator.py`(run_cycle: 게이트 통과 시 active 승격).
- 변경파일: 위 3개 + `tests/unit/test_{analyst,redteam}.py` + `tests/evals/test_seed_pipeline.py`(placeholder 대체).
- 완료기준: 씨앗 T-2026-0100이 RedTeam pass로 active, eval(falsifiers·dated evidence·전문 미인용) 통과. LLM 합성은 v1.x(결정성 위해 룰베이스).

### P5 제안+전달+뷰어 (AGENTS.md, SDD §6) — MVP 완성
- 목표: active 테제로 제안·위클리 브리핑 자동 생성 + 조회 API + 뷰어. GOLDEN RULE 2/5 강제.
- 산출: `agents/allocator.py`(시나리오/사이징/리스크, 명령형 금지), `agents/synthesizer.py`(위클리 Markdown, 링크+요약), `agents/curator.py`(예측 등록·캘리브레이션·신선도·아카이브), `services/advisory.py`(제안/브리핑 공용), `api/app.py`(FastAPI 조회, 매매 엔드포인트 없음), `viewer/app.py`(Streamlit 그래프·상세·제안·브리핑).
- 변경파일: 위 + dev deps(fastapi/httpx), mypy override(streamlit), `tests/unit/test_{allocator,synthesizer,curator}.py`, `tests/integration/test_api.py`, `tests/evals/test_advisory_discipline.py`.
- 완료기준: 제안·브리핑 자동생성(시나리오 포함), API 조회/그래프, eval(시나리오·리스크·링크전용·비명령형) 통과. PRD §8 성공기준 충족.
