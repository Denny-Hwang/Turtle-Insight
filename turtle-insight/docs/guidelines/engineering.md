# 엔지니어링 가이드라인

## 언어·도구
- Python 3.12. `ruff`(lint+format), `mypy --strict`, `pytest`. `pre-commit`로 강제.
- 모든 공개 함수에 타입 힌트. 도메인 모델은 `pydantic` v2.
- 의존성은 `pyproject.toml`(uv/pip). 잠금 파일 커밋.

## 레이어 규율
- `domain/`은 순수: IO·네트워크·전역 상태 금지. 부수효과는 `connectors/`·`storage/`·`services/`에만.
- 에이전트(`agents/`)는 비즈니스 로직 + **주입된** 의존성(레포지토리·inference·커넥터). 직접 import로 IO 만들지 않는다.
- LLM 호출은 `services/inference.py` 한 곳. 다른 곳에서 SDK 직접 호출 금지.
- 외부 소스 접근은 `connectors/`의 `Connector` 인터페이스로만.

## 설정·비밀
- 설정은 `config/settings.py`(pydantic-settings) 통해 env에서. 매직 값·경로·**모델명** 하드코딩 금지.
- 비밀(API 키 등)은 `.env`(gitignore) 또는 OS 키체인. **절대 커밋 금지.** PR 점검(R3).

## 커밋·브랜치·PR
- Conventional Commits: `feat: / fix: / docs: / test: / refactor: / chore:`.
- 단계(P0–P5)마다, 논리 단위마다 커밋. 거대 일괄 커밋 금지.
- PR 본문에 해당 단계·exit criteria 체크리스트. 설계 변경 시 SDD/TDD/ADR 동시 갱신.
- 결정에는 ADR 추가(`docs/adr/`).

## 로깅·오류
- 구조화 로깅(JSON). 에이전트 실행 id·소요·토큰·prompt_version 기록.
- 외부 호출 실패는 재시도+백오프 후 누락 플래그로 처리(파이프라인 중단 금지).

## 테스트
- 새 로직엔 테스트 동반. 게이트/상태기계/검증/캘리브레이션은 필수.
- 통합테스트는 **녹화 픽스처** 사용(라이브 외부 호출 금지). eval은 GOLDEN RULES 준수 검사.
- 도메인·게이트 커버리지 ≥ 90%.

## 데이터 위생
- 외부 텍스트는 링크 + ≤500자 사실 요약 + 메타만 저장(전문 금지). 소스 ToS 준수.
- 테제 정본은 `theses/*.yaml`(git). DB는 인덱스.
