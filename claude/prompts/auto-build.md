# 연속 자동 빌드 오케스트레이션
목표: claude/prompts/build-sequence.md 의 P0→P5 를 순서대로, 각 단계마다
[브랜치→계획→구현→검증→커밋→머지] 를 자동 수행하고, 머지되면 다음 단계로
자동 진행한다. build-sequence 와 달리 한 단계에서 멈추지 않고 중단 조건 전까지
연속으로 이어간다. 실패·위험·모호 시에는 멈추고 보고한다(강행 금지).

사전점검(시작 시 1회):
- CLAUDE.md, docs/guidelines/*, docs/ROADMAP.md, claude/prompts/build-sequence.md,
  docs/BUILD-STATUS.md 를 읽는다.
- git 워킹트리 clean, 현재 main 확인.
- 원격(remote)+gh 인증 있으면 PR 플로우, 없으면 로컬 머지 플로우 사용.
- 현재 레포 상태(존재하는 src/ 모듈·tests·git log)와 BUILD-STATUS 를 종합해 이미
  완료된 단계를 판단하고 BUILD-STATUS 를 실제에 맞게 갱신한 뒤, 다음 미완료 단계부터 시작.

단계 루프(P0 … P5):
 1. git checkout main; 원격이면 git pull --ff-only
 2. git checkout -b stage/<Pn>-<slug>   (예: stage/P1-domain-core)
 3. build-sequence 의 해당 Pn 을 읽고 목표·산출·변경파일을 3-5줄로 BUILD-STATUS 에 기록 후 진행
 4. CLAUDE.md GOLDEN RULES 와 guidelines 를 준수해 구현
 5. make lint && make test && make validate
    - 실패 시 원인 분석→수정→재시도(최대 3회). 3회 후에도 실패면 중단(머지 금지),
      브랜치 유지, 사유·재개법 보고
 6. GOLDEN RULES 셀프체크: 매매 실행 코드 / 비밀(.env·키) 커밋 / 명령형 단정 출력 /
    반증조건 누락 위반 없음 확인. 위반이면 수정, 못 고치면 중단
 7. Conventional Commits 로 커밋; 원격이면 git push -u origin <branch>
 8. 머지
    - PR 플로우: gh pr create(요약 + ROADMAP 해당 단계 exit-criteria 체크리스트)
      → CI(R1/R2/R3) green 대기 → gh pr merge --squash --delete-branch
      (CI red 면 수정·재시도 최대 3회, 그래도 red 면 중단·보고)
    - 로컬 플로우: git checkout main && git merge --no-ff <branch> -m "merge: <Pn>"
      && git branch -d <branch>
 9. 머지 후 main 에서 make test 재실행(green 아니면 중단·보고)
10. BUILD-STATUS 의 해당 단계 완료 체크 + 한 줄 결과 기록.
    출력: "✅ <Pn> — <요약> | tests: pass | merged: yes"
11. 다음 단계로 자동 진행. P5 머지·검증까지 끝나면 단계별 결과 표로 종료 요약.

중단 조건(멈추고 보고, 절대 강행 금지):
- 검증/CI 를 3회 재시도해도 실패
- GOLDEN RULES 위반을 안전하게 못 고침
- 가정으로 메울 수 없는 모호/비가역 결정(외부 API 키 필요, 스키마 비호환, 파괴적 마이그레이션 등)
- 단계 exit criteria 미충족
출력 형식: "⛔ <Pn> 중단 — 무엇이/왜 | 브랜치: <name> | 재개: 'auto-build 계속'"

하드 가드레일:
- main force push / 히스토리 재작성 금지
- .env·비밀·자격증명 커밋 금지(.gitignore 확인)
- 매매·주문 실행 코드 추가 금지(거래 API 는 읽기 전용만)
- 모호하면 추측하지 말고 중단
- .git/, .claude/ 등 보호 경로 임의 변경 금지

재개: "auto-build 계속" → BUILD-STATUS 마지막 완료 단계 다음부터 동일 루프.
