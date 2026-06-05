# SDD — Turtle Insight 시스템 설계

v0.1. 본 문서가 아키텍처의 권위 문서다. 상세 구현 설계는 `TDD.md`, 도메인 규칙은 `guidelines/thesis-and-epistemics.md`.

## 1. 아키텍처 개요

로컬 단일 호스트(Mac Mini)에서 도는 모듈러 모놀리스. 4개 면:

1. **수집(Ingestion)** — Scout가 외부 소스를 정규화해 `signals`로.
2. **분석(Analysis)** — 에이전트들이 시그널을 테제 그래프로 변환·검증.
3. **제안·전달(Advisory/Delivery)** — Allocator/Synthesizer가 제안·브리핑 생성.
4. **메모리·학습(Memory)** — Curator가 그래프·근거·캘리브레이션 유지.

```
[외부 소스] ─► Scout ─► signals
                          │ (라우팅)
        ┌─────────────────┼─────────────────┐
      Macro          Strategist        Analyst/Market
        └───────► Thesis Graph ◄───────┘
                          │ draft/candidate
                       RedTeam ─(pass)─► active
                          │
                    Allocator ─► Proposal ─► Synthesizer ─► Brief
                          │
                       Curator (track record / calibration / archive)
                          ▼
                   [Storage]  ◄──►  [API/FastAPI]  ──►  [Viewer/Streamlit]
```

## 2. 핵심 도메인 모델 — 테제 그래프

기본 단위 **Thesis**. 4계층: `macro | trend | chain | asset`. 노드는 부모/자식(인과)과 자산(KR/US 티커)으로 연결된 방향 그래프.

상태기계:
```
draft ──(근거·반증조건 충족)──► candidate ──(RedTeam pass)──► active
  active ──(반증조건 충족 관측)──► invalidated
  active ──(목표·시계 달성)──► realized
```
전이 규칙은 `domain/state.py`에 집중하고 단위테스트로 강제. `candidate→active`는 RedTeam `pass` 없이는 불가(GOLDEN RULE 3).

스키마: `schema/thesis.schema.yaml` (필드·필수조건의 단일 출처). 테제는 `theses/<status>/<id>.yaml` 파일이자 DB 레코드(content-as-code: 파일이 정본, DB는 인덱스/질의용 — TDD §동기화 참조).

## 3. 에이전트 오케스트레이션

- 각 에이전트는 `Agent.run(ctx)` 계약(AGENTS.md). 순수 로직 + 주입 의존성.
- **스케줄**: macOS `launchd` plist가 주기별로 진입점 호출 → 작업을 **Dramatiq**(Redis 브로커) 큐에 적재 → 워커가 실행. MVP는 Redis 없이 동기 실행 + cron도 허용(ROADMAP P1).
- **트리거**: 시그널 태그/실적 일정/사용자 요청. Scout가 라우팅 힌트를 부여하면 해당 분석 에이전트가 깨어난다.
- **멱등성**: 시그널·테제는 안정 id. 재실행이 중복 생성하지 않도록 upsert.

## 4. 추론(LLM) 레이어 — 티어링

`services/inference.py` 단일 게이트.
- **Deep tier** (Claude, Anthropic API): 테제 합성, RedTeam 반론, 브리핑 작문. 모델은 config(`TI_DEEP_MODEL`).
- **Fast tier** (선택, 로컬 Ollama/MLX): 시그널 태깅·요약·분류 등 고빈도 저가 작업. 미설정 시 deep으로 폴백.
- 모든 호출에 출처/프롬프트 버전 로깅. 모델 문자열 하드코딩 금지.

## 5. 데이터 레이어

### 소스(커넥터)
- KR: DART(공시), KRX(시세·지수), 한국은행 ECOS(매크로), 뉴스(링크+요약).
- US: SEC EDGAR(공시), FRED(매크로), 시장데이터 API(MVP `yfinance` → 운영 Polygon/Tiingo 등, *요금·약관 확인*), 실적 트랜스크립트.
- 글로벌: 원자재·전력·해운(트렌드 검증).
- 정성: 키노트 트랜스크립트.
- 각 커넥터는 `connectors/<source>.py`로 추상화(인터페이스 `Connector.fetch()`), 소스 교체가 도메인에 영향 없게.

### 저작권/프라이버시
링크 + 짧은 사실 요약 + 메타데이터만 저장. 전문 미저장(GOLDEN RULE 5). 비밀정보 env.

### 스토리지
- **MVP**: SQLite(관계형 인덱스) + 파일(`theses/*.yaml` 정본) + 로컬 파일 캐시.
- **v1+**: PostgreSQL + **pgvector**(근거 RAG: 시그널/문서 임베딩 검색). 시계열 시세는 Postgres 또는 Parquet.
- Redis: Dramatiq 브로커(v1+).
- 스키마 진화는 SQLAlchemy + Alembic.

## 6. 인터페이스

- **API (FastAPI)**: 로컬 전용. 테제 그래프 조회/탐색, 제안/브리핑 조회, 에이전트 수동 트리거, 캘리브레이션 메트릭. 인증은 로컬 토큰(단일 사용자).
- **Viewer (Streamlit)**: 테제 그래프 탐색, 테제 상세(근거·반증·확신도·트랙레코드), 제안/브리핑 열람. b-anki 경험 재활용.
- **Briefings**: Synthesizer가 Markdown 생성 → 옵션 PDF.

## 7. 배포 (Mac Mini 로컬)

- Docker Compose: `postgres`, `redis`(v1+). 앱(FastAPI/워커/Streamlit)은 로컬 venv 또는 컨테이너.
- `launchd`로 스케줄 진입점 구동. 로그는 로컬 파일 + 구조화 로깅.
- 단일 사용자·로컬 네트워크. 외부 노출 없음(노출 시 Tailscale 등은 v2 검토).

## 8. 시퀀스 예 — 씨앗 테제 1주기

1. Scout: 키노트·HBM 수요·전력 관련 시그널 적재(링크+요약).
2. Strategist/Analyst: Chain 테제(가속컴퓨팅 풀스택 병목)와 자산 후보 테제 생성(status=candidate), 근거에 시그널 링크, falsifiers 명시.
3. RedTeam: 베어 케이스·반증조건 점검 → `pass`면 active, `revise`면 반려.
4. Allocator: active 테제 + 위험성향 → 강세/기본/약세 시나리오·사이징 논리 제안.
5. Synthesizer: 위클리 브리핑 작성.
6. Curator: 예측 등록, 이후 실현 여부로 캘리브레이션 채점.

## 9. 횡단 관심사

- **관측성**: 에이전트 실행/추론 호출 구조화 로그, 캘리브레이션 메트릭.
- **테스트성**: 도메인·게이트 로직은 IO와 분리(TDD §테스트 전략).
- **확장성**: 새 소스=새 커넥터, 새 분석=새 에이전트. 그래프 모델은 불변.

(아키텍처 결정 근거: `docs/adr/README.md`.)
