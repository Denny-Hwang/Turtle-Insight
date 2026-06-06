# 아키텍처 결정 기록 (ADR)

결정마다 항목을 추가한다(번호·제목·상태·맥락·결정·결과). 새 결정은 PR과 함께.

---

## ADR-0001 — 테제 그래프를 1차 도메인 모델로 채택
- **상태**: accepted
- **맥락**: 상위(철학)·기본(트렌드/가치사슬)·하위(기업/기술)의 3계층 분석을 일관되게 표현하고, 위→아래 인과와 아래→위 증거를 양방향 탐색해야 한다.
- **결정**: 모든 분석 산출을 4계층 `Thesis` 노드 + 부모/자식·자산 링크의 방향 그래프로 모델링한다.
- **결과**: 어느 노드에서든 위아래 탐색 가능("전방위 가이드"). 새 분석은 새 에이전트가 그래프를 갱신할 뿐 모델은 불변.

## ADR-0002 — 매매 미실행 + 분석/결정 분리
- **상태**: accepted
- **맥락**: 자동 매매는 큰 리스크이고, 도구의 목적은 *판단 지원*이다.
- **결정**: 주문 실행 기능을 만들지 않는다. 거래 API는 읽기 전용만. 산출물은 시나리오·리스크가 달린 제안으로 강제(코드·eval).
- **결과**: 안전·책임 경계 명확. 실행은 사람. GOLDEN RULES에 고정.

## ADR-0003 — 추론 엔진 티어링 (Claude deep + 선택적 로컬 fast)
- **상태**: accepted
- **맥락**: Mac Mini 로컬, 비용·속도. 고빈도 작업(태깅/요약)과 심층 작업(테제 합성/반론)의 성격이 다르다.
- **결정**: `services/inference.py` 단일 게이트로 deep(Claude, config 모델)과 fast(로컬 Ollama/MLX, 미설정 시 deep 폴백)를 분리.
- **결과**: 비용 통제·교체 용이. 모델명 하드코딩 금지.

## ADR-0004 — content-as-code (테제 정본=git 파일, DB=인덱스)
- **상태**: accepted
- **맥락**: 결정·근거 변화의 재현성과 추적성이 중요(밀레니엄-랩 규율 계승).
- **결정**: 테제 정본은 `theses/<status>/<id>.yaml`. DB는 질의·그래프 인덱스로 단방향 동기화. CI(R1)가 불일치 검사.
- **결과**: git 이력으로 사고 추적, DB로 성능. 단, 동기화 규율 필요.

## ADR-0005 — MVP는 SQLite, v1+는 PostgreSQL+pgvector
- **상태**: accepted
- **맥락**: MVP는 단순·빠르게. 근거 RAG·임베딩 검색은 이후 필요.
- **결정**: MVP SQLite + 파일. v1+에서 Postgres+pgvector로 전환(SQLAlchemy/Alembic로 진화).
- **결과**: 초기 마찰 최소화, 확장 경로 확보.

## ADR-0006 — MVP DB는 무손실 인덱스(테제 전체 저장, edges 비정규화 보류)
- **상태**: accepted
- **맥락**: P2 동기화의 exit criteria는 "예시 테제가 파일↔DB 왕복". 정본은 파일(ADR-0004)이지만, 왕복 검증과 조회를 위해 DB가 테제를 충실히 복원할 수 있어야 한다. TDD §4의 `theses` 컬럼 목록은 `falsifiers`/`risks`/`parents`/`children`을 포함하지 않고, 그래프는 `thesis_edges` 테이블로 분리한다.
- **결정**: MVP에서는 `theses` 행에 `parents`/`children`/`falsifiers`/`risks`를 JSON 컬럼으로, `assets`/`evidence`를 자식 테이블로 저장해 **무손실 인덱스**로 만든다. 정규화된 `thesis_edges` 테이블은 그래프 질의가 필요해지는 시점(P5/v1.x)으로 보류한다. 파일↔DB는 단방향(`make sync`), CI(`make sync-check`)가 왕복 일관성을 검사한다.
- **결과**: 왕복 충실도 확보·구현 단순. 그래프 탐색은 JSON의 parents/children id로 충분(P5 `/theses/{id}/graph`). edges 정규화는 RAG/대규모 그래프 질의 도입 시 재검토.

## ADR-0007 — 3계층 자동화(Macro/Strategist/Market) + Market 산출 형태
- **상태**: accepted
- **맥락**: v1.x에서 상위(Macro)·기본(Strategist)·기술(Market) 계층을 자동화해 macro→trend→chain 그래프를 완성해야 한다. Macro/Strategist는 테제를, Market은 "기술/시장 신호"를 산출(AGENTS.md). MVP의 결정성(CI 재현성)을 유지해야 한다.
- **결정**: Macro/Strategist/Analyst는 공용 `agents/templates.py`(ThesisTemplate+build_candidate+synthesize)로 **결정적 룰베이스** 합성(시그널 매칭→evidence 링크, falsifiers 명시). 계층 간 parent/child 링크로 그래프 연결(0001→0002→0100). Market은 테제가 아니라 **파생 시장국면 신호**(regime·KR/US 상대강도, 링크+요약)를 `signals`에 적재. `Orchestrator.run_full_cycle`이 Scout→Macro→Strategist→Analyst→Market→RedTeam→승격을 구동(`run_cycle`은 MVP 호환 유지). LLM 합성은 이후.
- **결과**: 3계층이 게이트를 통과해 active가 되는 연결 그래프 자동 생성. 기존 P0–P5 테스트 불변(run_cycle 유지). Market 신호는 추후 Allocator 국면 반영에 활용 가능.

## ADR-0008 — PostgreSQL + pgvector 전환 경로 (v1+)
- **상태**: accepted
- **맥락**: ADR-0005대로 v1+는 Postgres + pgvector(근거 RAG). 단일 코드베이스가 SQLite(dev)와 Postgres(v1+)를 모두 지원하고, 스키마 진화는 Alembic으로 추적해야 한다. CI에서 결정적으로 검증 가능해야 한다.
- **결정**: (1) 리포지토리는 SQLAlchemy 엔진 기반이라 `from_url`로 SQLite/Postgres 공용 — 관계형 코어 테이블은 두 DB에서 동일. (2) 마이그레이션은 Alembic(`alembic upgrade head`, `make migrate`); 초기 리비전은 모델 메타데이터로 테이블 생성(이후 컬럼 단위 autogenerate). (3) **pgvector는 Postgres 전용**: `storage/rag.py`의 `VectorStore`가 `vector` 확장+`embeddings` 테이블을 별도 관리(공용 Base 밖). 벡터는 텍스트로 전달 후 `::vector` 캐스트 → 추가 파이썬 드라이버 의존 없음(psycopg만). 임베딩은 외부 모델이 공급. (4) CI `pg-compat` 잡이 pgvector 이미지 서비스로 마이그레이션+왕복+근접검색을 검증; 로컬 SQLite 테스트는 `TI_TEST_PG_URL` 없으면 skip. docker-compose로 postgres+redis 제공.
- **결과**: SQLite 경로 무변경(회귀 없음)으로 Postgres+pgvector를 추가. RAG 검색 substrate 확보. 임베딩 모델 연동·시계열 시세는 후속.
