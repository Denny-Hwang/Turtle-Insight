# ROADMAP — Turtle Insight 단계별 빌드

각 단계는 `claude/prompts/build-sequence.md`의 동일 번호 프롬프트로 Claude Code가 실행한다. 한 번에 한 단계, 단계마다 커밋, exit criteria 충족 후 다음 단계.

| 단계 | 이름 | 산출물 | Exit criteria |
|---|---|---|---|
| **P0** | 부트스트랩 | 레포 스캐폴드(`src/`, `tests/`, Makefile, ruff/mypy/pytest, pre-commit, CI 골격, settings) | `make setup/lint/test` 통과, 빈 테스트 그린, CI 동작 |
| **P1** | 도메인 코어 | `domain/`(Thesis 등 모델, state.py 상태기계, calibration.py), `schema/` 검증(`validation.py`=R1), 단위테스트 | 게이트·전이 테스트 통과, R1이 `theses/examples` 검증 통과 |
| **P2** | 저장 + 동기화 | `storage/`(files 정본, sqlite_repo, sql_models), `make sync`, files↔db 통합테스트 | 예시 테제가 파일↔DB 왕복, 상태 이동 시 폴더 이동 |
| **P3** | 수집 + 추론 게이트 | `connectors/`(MVP: edgar/dart/fred/market_api/news, 픽스처), `services/inference.py`(deep/fast), Scout | Scout가 픽스처에서 시그널 적재(링크+요약), inference 목 테스트 |
| **P4** | 분석 + 게이트 | Analyst, RedTeam, 오케스트레이터 1주기. 씨앗 테제가 candidate→(RedTeam)→active | 씨앗 테제가 게이트 통과해 active, eval 통과(falsifiers·시나리오·전문 미인용) |
| **P5** | 제안 + 전달 + 뷰어 | Allocator(제안), Synthesizer(위클리 브리핑), Curator(트랙레코드), FastAPI 조회, Streamlit 뷰어 | 위클리 브리핑·제안 자동 생성(시나리오 포함), 뷰어에서 그래프·테제 탐색 |

**MVP(v1.0) = P0–P5 완료.** 성공 기준은 `PRD.md §8`.

## 이후 (v1.x+)

- Macro/Strategist/Market 에이전트 확장(상위·기본·기술 계층 자동화)
- PostgreSQL + pgvector 전환(근거 RAG), Dramatiq+Redis 비동기, launchd 스케줄 정식화
- 로컬 모델 티어링(Ollama/MLX) 실측 적용
- 캘리브레이션 히스토리 대시보드, 데일리/먼슬리 브리핑
- 다국가 소스 확장, (옵션) 증권사 **읽기 전용** 연동
- 외부 접근 필요 시 Tailscale 등 (기본은 로컬 전용)

## 운영 원칙

- 스코프 변경은 ADR 추가(`docs/adr/`).
- 새 단계 진입 전 직전 단계 exit criteria를 PR 체크리스트로 확인.
- GOLDEN RULES(특히 무매매·제안형·반증조건)는 어떤 단계에서도 깨지 않는다.
