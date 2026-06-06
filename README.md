# Turtle Insight

> 메가트렌드를 **상위(문명·철학) → 기본(트렌드·가치사슬) → 하위(기업·기술·시장)** 3계층으로 분해하고, 각 계층의 **투자 테제(Thesis)** 를 근거·반증조건과 함께 그래프로 연결해, Mac Mini 로컬 AI 에이전트가 지속적으로 수집·검증·반박·갱신하며 **투자 방향 제안과 정기 브리핑**을 생성하는 개인용 의사결정 지원 시스템.

이름의 함의: 거북이 — 장수·인내·"천천히, 오래, 멀리". 장기(5–20년) 호흡의 투자 철학을 담는다.

> ⚠️ **Turtle Insight는 투자 *결정 지원* 도구이며, 자동 매매를 하지 않는다.** 산출물은 근거·리스크·시나리오가 달린 *제안*이지 매수/매도 *지시*가 아니다. 면허 있는 투자자문이 아니며, 최종 판단·실행은 사람이 한다. (→ `docs/guidelines/thesis-and-epistemics.md`)

---

## 이 레포를 읽는 순서

1. **`docs/PRD.md`** — 무엇을, 왜, 누구를 위해. 범위와 MVP 정의.
2. **`docs/SDD.md`** — 시스템 설계(아키텍처, 테제 그래프, 데이터, 에이전트, 배포).
3. **`docs/TDD.md`** — 상세 기술 설계(모듈·인터페이스·DB·API·테스트 전략).
4. **`AGENTS.md`** — 분석 파이프라인 에이전트 명세.
5. **`CLAUDE.md`** — Claude Code가 이 레포에서 일하는 방식(필독·작업 규칙).
6. **`docs/ROADMAP.md` + `claude/prompts/build-sequence.md`** — 단계별 개발 실행.

## 디렉터리 구조

```
turtle-insight/
  README.md                         # 이 파일
  CLAUDE.md                         # Claude Code 작업 규칙 (golden rules 포함)
  AGENTS.md                         # 분석 에이전트 로스터
  docs/
    PRD.md                          # 제품 요구사항
    SDD.md                          # 시스템 설계
    TDD.md                          # 상세 기술 설계 + 테스트 전략
    ROADMAP.md                      # 단계별 빌드 계획
    masterplan-v0.1.md              # (추가 예정) 비전·기원 문서
    guidelines/
      engineering.md                # 코딩·레포 규율
      thesis-and-epistemics.md      # 도메인 가드레일(테제·확신도·반증·무매매)
    adr/
      README.md                     # 아키텍처 결정 기록(ADR) 인덱스 + 시드
  schema/
    thesis.schema.yaml              # 테제 스키마(content-as-code)
  theses/
    candidates/                     # 검증 중 테제
    active/                         # 검증 통과 테제
    archive/                        # 반증·실현 종료 테제
    examples/                       # 작동 예시
  claude/
    prompts/
      build-sequence.md             # 단계별 Claude Code 빌드 프롬프트(P0–P5)
  src/turtle_insight/               # (P0에서 생성) 애플리케이션 코드
  tests/                            # (P0에서 생성)
```

> 기존 `polaris-masterplan-v0.1.md`는 코드네임을 **Turtle Insight**로 갱신해 `docs/masterplan-v0.1.md`로 추가할 것. 본 레포의 설계 권위 문서는 `SDD.md`이며, master plan은 비전·기원 기록으로 보존한다.

## 빠른 시작 (Quickstart)

```bash
make setup            # 의존성 설치(uv) + pre-commit 훅
make analyze          # 분석 1주기를 DB에 적재 (macro→trend→chain, 픽스처 기반)
make run-viewer       # Streamlit 뷰어 (그래프·테제 상세·제안·브리핑)
# 또는
make run-api          # FastAPI 조회 API (/theses, /theses/{id}/graph, /proposals/latest,
                      #                    /briefs/{daily,weekly,monthly}, /calibration, /market/regime)
```

> 뷰어가 "No theses in the DB yet"를 보이면 먼저 **`make analyze`** 를 실행해 DB(`TI_DB_URL`, 기본 `sqlite:///ti.db`)를 채운다.

기타 명령: `make lint` · `make test` · `make validate`(R1) · `make sync`/`sync-check` · `make scorecard`(R4) · `make migrate`(Alembic) · `make up`(docker compose: postgres+redis).

## 상태

- **MVP(P0–P5) 완료** + **v1.x**: P6 3계층 자동화(Macro/Strategist/Market), P7 캘리브레이션·스코어카드,
  P8 데일리/먼슬리 브리핑, P9 시장국면 반영, P10 PostgreSQL+pgvector(CI 검증), P11 LLM 어댑터(Ollama/Anthropic).
- 진행 추적: `docs/BUILD-STATUS.md`.

## 스택 요약

Python 3.12 · FastAPI · SQLite(MVP) → PostgreSQL+pgvector · SQLAlchemy/Alembic · Dramatiq+Redis · Streamlit(뷰어) · Docker Compose · launchd(스케줄) · Anthropic API(심층 추론, 모델은 config) + 선택적 로컬 모델(Ollama/MLX, 고빈도 경량 작업).
