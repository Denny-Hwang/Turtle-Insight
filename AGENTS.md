# AGENTS.md

Turtle Insight의 **분석 파이프라인 에이전트**. 각 에이전트는 입력을 받아 테제 그래프를 갱신하거나 산출물을 만드는 애플리케이션 컴포넌트다. (개발/CI 자동화인 *Claude Code Routines*는 `CLAUDE.md §5` 참조 — 별개 개념.)

공통 계약: 모든 에이전트는 `agents/base.py`의 `Agent` 인터페이스를 구현한다 — `run(ctx) -> AgentResult`. 부수효과는 주입된 `connectors`/`storage`/`inference`를 통해서만. 추론 호출은 `services/inference.py` 경유.

| # | 에이전트 | 계층 | 책임 | 주기 | MVP |
|---|---|---|---|---|---|
| 1 | **Scout** | — | 뉴스·공시(DART/EDGAR)·실적·키노트·매크로·시세를 수집·정규화·태깅하고 `signals` 테이블에 적재. 라우팅 힌트 부여. | 일/장중 | ✅ |
| 2 | **Macro** | 상위 | 문명·기술확산·인구·에너지·지정학의 장기 호를 종합해 Macro 테제 생성/갱신. | 월/분기 | ✅ (v1.x) |
| 3 | **Strategist** | 기본 | 메가트렌드를 산업 가치사슬로 매핑해 Trend/Chain 테제 생성. 부모(Macro)·자식(Asset) 링크 구성. | 주 | ✅ (v1.x) |
| 4 | **Analyst** | 하위 | 기업/산업 펀더멘털(재무·경쟁우위·밸류에이션)로 Asset 테제 생성·검증. 트리거된 시그널 처리. | 실적·트리거 | ✅ |
| 5 | **Market** | 하위 | 가격·거래량·추세, 시장국면(위험선호/회피), KR↔US 상대강도 등 기술/시장 신호. | 일 | ✅ (v1.x) |
| 6 | **RedTeam** | 전계층 | 모든 테제 변경에 대해 베어 케이스·반증조건 점검·확증편향 플래그. **통과 전 `active` 불가.** | 테제 변경 시 | ✅ |
| 7 | **Allocator** | — | 생존(active) 테제 + 사용자 제약(위험성향·시계·제외)으로 워치리스트/배분 *제안* 생성. 시나리오·포지션 사이징 논리 포함. 매수 지시 아님. | 일/주 | ✅ |
| 8 | **Synthesizer** | — | 데일리/위클리/먼슬리/온디맨드 브리핑(Markdown→옵션 PDF) 생성. | 일/주/월 | ✅ |
| 9 | **Curator** | — | 테제 그래프·증거 아카이브 유지, 캘리브레이션 트랙레코드 채점, 오래된 근거 플래그. | 상시 | ✅ |

## 데이터 흐름

```
Scout ─► signals ─►(라우팅)─► Macro / Strategist / Analyst / Market
                                          │
                                   thesis 생성/갱신 (status=draft|candidate)
                                          │
                                       RedTeam ──(통과)──► status=active
                                          │
                              Allocator ─► 제안  ─► Synthesizer ─► 브리핑
                                          │
                                       Curator (트랙레코드·캘리브레이션·아카이브)
```

## 에이전트별 I/O 계약(요약)

- **Scout** → `Signal{ source, url, published_at, summary, tickers[], tags[], raw_ref }` (전문 미저장, 링크+요약만).
- **Macro/Strategist/Analyst/Market** → `Thesis`(스키마: `schema/thesis.schema.yaml`). 근거에는 출처 시그널 id를 링크.
- **RedTeam** → `Review{ thesis_id, bear_case, falsifier_check, bias_flags[], verdict: pass|revise|reject }`.
- **Allocator** → `Proposal{ generated_at, items:[{thesis_id, asset, stance, scenarios{bull,base,bear}, sizing_rationale, risks[]}], constraints_snapshot }`.
- **Synthesizer** → `Brief{ kind: daily|weekly|monthly|deepdive, body_md, sources[] }`.
- **Curator** → `CalibrationScore`, 아카이브 이동, 근거 신선도 플래그.

> MVP(P0–P5)는 Scout/Analyst/RedTeam/Allocator/Synthesizer/Curator로 **씨앗 테제 1줄기**를 끝까지 돌린다. Macro/Strategist/Market은 **v1.x(P6)에서 구현 완료** — `run_full_cycle`로 macro→trend→chain 3계층 그래프를 자동 생성한다(룰베이스, 결정적). (→ `docs/ROADMAP.md`)
