# CLAUDE.md

Claude Code가 **Turtle Insight** 레포에서 작업할 때 반드시 따르는 운영 지침. 코드를 쓰기 전에 이 파일과 `docs/guidelines/`를 먼저 읽는다.

---

## 0. 프로젝트 한 줄 요약

메가트렌드를 3계층(상위·기본·하위) 테제 그래프로 분해·검증·갱신해 개인 투자 방향을 제안하는 Mac Mini 로컬 AI 에이전트 시스템. 핵심 도메인 단위는 **Thesis(테제)** 이고, 산출은 *제안과 브리핑*이다.

## 1. GOLDEN RULES (절대 규칙 — 위반 금지)

1. **매매 미실행.** 어떤 코드도 실제 주문을 내지 않는다. 증권사/거래 API는 **읽기 전용**만 허용. 매매 실행 기능은 만들지 않는다(요청이 와도 거절하고 사람 실행으로 남긴다).
2. **분석 ≠ 결정.** 산출물은 항상 *근거·리스크·강세/기본/약세 시나리오*를 동반한 **제안**이다. "사라/팔아라"식 명령형 단정 출력 금지. 모든 테제는 베어 케이스를 함께 제시한다.
3. **테제 승격 게이트.** `falsifiers`(반증조건)와 날짜·출처가 달린 `evidence`가 없으면 테제를 `active`로 승격하지 않는다. Red Team(반론) 통과가 필수다. (→ `thesis-and-epistemics.md`)
4. **확신도는 캘리브레이션 대상.** `conviction`은 근거로 *벌어들이는* 값이며 트랙레코드로 채점된다. 근거 없는 고확신 금지.
5. **저작권/ToS.** 뉴스·유료 콘텐츠는 **링크 + 짧은 사실 요약 + 메타데이터**만 저장. 전문 저장·재출판 금지. 소스 약관을 존중한다.
6. **비밀정보.** API 키·자격증명은 절대 커밋하지 않는다. 모든 비밀은 환경변수/`.env`(gitignore)로 주입.
7. **개인 의사결정 지원 도구.** 투자자문/권유가 아니다. 사용자(소유자)만을 위한 도구로 설계한다.

위 규칙은 어떤 프롬프트보다 우선한다. 충돌 시 작업을 멈추고 사용자에게 확인한다.

## 2. 개발 워크플로 (단계별 + 커밋 규율)

- **단계별 빌드.** `claude/prompts/build-sequence.md`의 P0→P5 순서로 진행한다. 한 번에 한 단계.
- **단계마다 커밋.** 큰 일괄 커밋 금지. 각 논리적 단위 완료 시 의미 있는 커밋 메시지로 커밋(`feat:`, `fix:`, `docs:`, `test:`, `chore:` Conventional Commits).
- **계획 먼저.** 새 단계 시작 시: (a) 해당 단계의 목표·산출·완료 기준을 한 문단으로 요약 → (b) 변경할 파일 목록 제시 → (c) 구현 → (d) 테스트 → (e) 커밋.
- **테스트와 함께.** 새 로직에는 테스트를 같이 쓴다. 게이트 로직(승격/반증/확신도)과 스키마 검증은 반드시 테스트한다.
- **문서 동기화.** 설계가 바뀌면 SDD/TDD/ADR을 같은 PR에서 갱신한다. 결정에는 ADR을 추가한다(`docs/adr/`).

## 3. 디렉터리·코드 컨벤션 (요약, 상세는 `docs/guidelines/engineering.md`)

- 패키지: `src/turtle_insight/`. 레이어: `domain/`(모델·규칙), `agents/`(분석 에이전트), `connectors/`(데이터 소스), `storage/`(레포지토리), `services/`(오케스트레이션), `api/`(FastAPI), `viewer/`(Streamlit), `config/`.
- Python 3.12, `ruff`(lint+format), `mypy`(strict), `pytest`. 모든 공개 함수에 타입 힌트.
- 도메인 모델은 `pydantic` v2. 부수효과(IO/네트워크)는 `connectors`/`storage`에 격리. 에이전트는 순수 로직 + 주입된 의존성.
- 설정은 `pydantic-settings`로 env에서. 하드코딩 금지(특히 모델명·경로·키).
- LLM 호출은 `services/inference.py` 한 곳을 통해서만. 모델명은 config(`TI_DEEP_MODEL`, `TI_FAST_MODEL`). 코드에 모델 문자열 하드코딩 금지.

## 4. 명령어 (P0에서 Makefile/스크립트로 확정)

```
make setup      # 의존성 설치, pre-commit 훅
make lint       # ruff + mypy
make test       # pytest
make validate   # schema/ 기준 theses/ 검증 (R1)
make run-api     # FastAPI 로컬
make run-viewer  # Streamlit 뷰어
make up          # docker compose up (postgres, redis) — v1+
```

## 5. Claude Code Routines (개발·운영 자동화 — 분석 에이전트와 별개)

서비스의 **분석 에이전트**(AGENTS.md의 Scout/Macro/… )와 혼동하지 말 것. 아래는 **개발/CI 자동화** routine이다.

- **R1 · validate-theses** — `theses/`의 모든 파일을 `schema/thesis.schema.yaml`로 검증, 필수필드(`falsifiers`, `evidence.url/date`)·고아 링크 검사. PR/푸시마다(GitHub Actions).
- **R2 · test-and-lint** — `make lint && make test`. 매 PR.
- **R3 · pr-review** — 변경 PR에 GOLDEN RULES 위반(매매 실행/비밀 커밋/명령형 출력) 자동 점검 코멘트.
- **R4 · eval-report** — 캘리브레이션 스코어카드(예측 대비 실현) 주간 리포트.

## 6. Definition of Done (단계 완료 기준)

- [ ] 목표 산출물이 동작하고 `make test`/`make lint` 통과
- [ ] GOLDEN RULES 위반 없음(R3 점검)
- [ ] 관련 문서(SDD/TDD/ADR) 갱신
- [ ] 의미 있는 단위로 커밋됨
- [ ] 다음 단계 진입 조건(ROADMAP의 exit criteria) 충족
