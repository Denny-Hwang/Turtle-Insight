# TDD — Turtle Insight 상세 기술 설계

v0.1. SDD의 아키텍처를 구현 수준으로 구체화한다(모듈·인터페이스·DB·API·테스트). 코드 작성 시 본 문서와 `engineering.md`를 따른다.

## 1. 패키지 레이아웃

```
src/turtle_insight/
  config/settings.py        # pydantic-settings (env)
  domain/
    thesis.py               # Thesis, Evidence, Falsifier (pydantic v2)
    signal.py               # Signal
    proposal.py             # Proposal, Brief, Review
    state.py                # 상태기계 전이 규칙(순수)
    calibration.py          # 트랙레코드 채점(순수)
  agents/
    base.py                 # Agent 인터페이스, AgentContext, AgentResult
    scout.py analyst.py redteam.py allocator.py synthesizer.py curator.py
    macro.py strategist.py market.py     # v1.x
  connectors/
    base.py                 # Connector 인터페이스
    dart.py edgar.py fred.py krx.py market_api.py news.py
  storage/
    repository.py           # ThesisRepository, SignalRepository (인터페이스)
    sqlite_repo.py          # MVP 구현
    sql_models.py           # SQLAlchemy 모델 (v1+ postgres 공유)
    files.py                # theses/*.yaml 읽기/쓰기(정본)
  services/
    inference.py            # LLM 게이트(deep/fast 티어)
    orchestrator.py         # 에이전트 실행/트리거
    validation.py           # 스키마 검증(R1)
  api/app.py                # FastAPI
  viewer/app.py             # Streamlit
tests/
  unit/ integration/ evals/
```

## 2. 도메인 모델 (pydantic v2)

```python
# domain/thesis.py
from enum import Enum
from datetime import date, datetime
from pydantic import BaseModel, Field, HttpUrl, conint

class Layer(str, Enum): macro="macro"; trend="trend"; chain="chain"; asset="asset"
class Horizon(str, Enum): short="short"; long="long"
class Status(str, Enum):
    draft="draft"; candidate="candidate"; active="active"
    invalidated="invalidated"; realized="realized"

class Evidence(BaseModel):
    date: date
    source: str
    url: HttpUrl
    summary: str = Field(max_length=500)   # 짧은 사실 요약만 (전문 금지)
    weight: float = Field(ge=0, le=1, default=0.5)
    signal_id: str | None = None

class AssetLink(BaseModel):
    market: str          # "KR" | "US" | ...
    ticker: str
    role: str            # "primary" | "secondary"

class Thesis(BaseModel):
    id: str              # "T-2026-0001"
    layer: Layer
    horizon: Horizon
    title: str
    claim: str
    conviction: conint(ge=0, le=100) = 0
    status: Status = Status.draft
    parents: list[str] = []
    children: list[str] = []
    assets: list[AssetLink] = []
    evidence: list[Evidence] = []
    falsifiers: list[str]            # 필수, 빈 리스트 불가(검증에서 강제)
    risks: list[str] = []
    review_cadence: str = "monthly"
    last_reviewed: date | None = None
    created: datetime
```

`Review`, `Proposal`, `Brief`, `Signal`는 각 모듈에 동형으로 정의(AGENTS.md 계약 따름).

## 3. 상태기계 (domain/state.py — 순수, 테스트 1급)

```python
def can_promote_to_active(t: Thesis, review: Review) -> bool:
    return (
        bool(t.falsifiers)
        and all(e.url and e.date for e in t.evidence)
        and len(t.evidence) >= 1
        and review.verdict == "pass"
    )
```
허용 전이 표만 `ALLOWED_TRANSITIONS`로 두고 그 외 전이는 예외. `candidate→active`는 위 게이트 필수(GOLDEN RULE 3).

## 4. 저장·동기화 (content-as-code)

- 정본은 `theses/<status>/<id>.yaml`. 상태 변경 시 파일을 해당 폴더로 이동(`files.move`).
- DB(SQLite/Postgres)는 질의·그래프 탐색용 **인덱스**. `files → db` 단방향 동기화(`make sync`), CI(R1)가 불일치 검사.
- 이유: git 이력이 결정·근거 변화를 추적(재현성). DB는 성능.

### DB 스키마(요지)
```
theses(id PK, layer, horizon, status, conviction, title, claim, created, last_reviewed)
thesis_edges(parent_id FK, child_id FK)           -- 그래프
thesis_assets(thesis_id FK, market, ticker, role)
evidence(id PK, thesis_id FK, date, source, url, summary, weight, signal_id)
signals(id PK, source, url, published_at, summary, raw_ref, tags JSON)
reviews(id PK, thesis_id FK, verdict, bear_case, bias_flags JSON, created)
proposals(id PK, generated_at, body JSON, constraints_snapshot JSON)
briefs(id PK, kind, created, body_md, sources JSON)
calibration(thesis_id FK, predicted JSON, realized JSON, score, scored_at)
```
(v1+ Postgres: `evidence`/`signals`에 pgvector `embedding` 컬럼 추가, RAG 검색.)

## 5. 추론 게이트 (services/inference.py)

```python
class Inference:
    def deep(self, messages, *, system=None, prompt_version): ...   # Claude (TI_DEEP_MODEL)
    def fast(self, messages, ...): ...                               # local model or fallback->deep
```
- 모델명은 settings에서. 호출마다 `prompt_version`·토큰·소스 로깅.
- 프롬프트는 `claude/prompts/` 또는 `agents/prompts/`에 버전 관리(코드에 인라인 금지).
- 구조화 출력이 필요하면 "JSON만 반환" 지시 후 안전 파싱(코드펜스 제거 → `json.loads` → 검증).

## 6. API (api/app.py, FastAPI)

```
GET  /theses?status=&layer=&ticker=         # 목록/필터
GET  /theses/{id}                            # 상세(+근거·반증·트랙레코드)
GET  /theses/{id}/graph                      # 부모/자식 서브그래프
POST /agents/{name}/run                       # 수동 트리거(로컬)
GET  /proposals/latest
GET  /briefs?kind=
GET  /calibration                             # 스코어카드
```
로컬 단일 사용자 토큰 인증. 매매/주문 엔드포인트는 **존재하지 않는다.**

## 7. 테스트 전략

- **단위(unit/)**: 도메인 모델·상태기계·캘리브레이션·검증 로직. 게이트(`can_promote_to_active`)는 양/음성 케이스 필수. 커넥터/추론은 목(mock).
- **통합(integration/)**: 커넥터(녹화된 픽스처 사용, 라이브 호출 금지), 저장 동기화(files↔db), 오케스트레이터 1주기 스모크.
- **eval(evals/)**: 추론 의존 산출물의 *규율* 검증 —
  - 모든 `active` 후보 테제에 `falsifiers`·dated evidence 존재(R1과 동일 규칙).
  - Allocator 출력이 명령형 단정이 아니라 시나리오/리스크를 포함(GOLDEN RULE 2) — 출력 구조 검사.
  - 브리핑이 전문 인용 없이 링크+요약만 사용(GOLDEN RULE 5).
- **CI**: `make lint`(ruff+mypy strict) → `make test` → `make validate`(R1). PR에서 R3가 GOLDEN RULES 위반 점검.
- 목표 커버리지: 도메인/게이트 로직 ≥ 90%.

## 8. 설정(env)

```
TI_DEEP_MODEL=...            # config로만, 코드 하드코딩 금지
TI_FAST_MODEL=...            # 선택(로컬). 미설정 시 deep 폴백
ANTHROPIC_API_KEY=...        # .env, gitignore
TI_DB_URL=sqlite:///ti.db    # v1+ postgres://...
TI_REDIS_URL=...             # v1+
DART_API_KEY=... FRED_API_KEY=... MARKET_API_KEY=...
```

## 9. 오류·관측성

- 외부 호출은 재시도+백오프, 실패 시 시그널 누락 플래그(분석 차단 아님).
- 구조화 로깅(JSON), 에이전트 실행 id·소요·토큰. 캘리브레이션 메트릭 주간 집계(R4).
