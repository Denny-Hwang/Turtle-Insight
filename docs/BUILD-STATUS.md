# BUILD STATUS
auto-build 가 이 파일로 진행 상태를 추적/재개한다.

| 단계 | 완료 | 머지 | 결과 한 줄 |
|---|---|---|---|
| P0 부트스트랩 | [x] | [x] | 레포 스캐폴드(uv/py3.12, src 41모듈, ruff+mypy, CI R1/R2) — PR #2, CI green |
| P1 도메인 코어 | [x] | [x] | domain 모델/상태기계/캘리브레이션 + R1 검증, 단위테스트 그린, examples 검증 통과 |
| P2 저장+동기화 | [ ] | [ ] | |
| P3 수집+추론 게이트 | [ ] | [ ] | |
| P4 분석+게이트(씨앗 테제 active) | [ ] | [ ] | |
| P5 제안+전달+뷰어(MVP) | [ ] | [ ] | |

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
