# Codex CLI — First Session

## 목적

빈 저장소 또는 문서만 있는 저장소에서 Codex에게 첫 개발 작업을 시킬 때 사용한다.
Codex를 프로젝트 루트에서 시작한 뒤 아래 프롬프트를 전달한다.

---

## First Prompt

```text
이 저장소는 B2B AI Performance Marketing SaaS의 MVP다.

먼저 다음 파일을 순서대로 읽어라.

1. AGENTS.md
2. docs/PRD.md
3. docs/ARCHITECTURE.md
4. docs/DATA_MODEL.md
5. docs/API_CONTRACT.md
6. docs/AI_COST_AND_CREDITS.md
7. docs/TESTING.md
8. TASKS.md

이번 세션의 범위는 TASKS.md의 Phase 0만이다.
Phase 1 이후 기능은 구현하지 마라.

작업 순서:
1. 현재 repository 상태와 local toolchain을 확인한다.
2. AGENTS.md 및 문서와 충돌하는 사항이 있으면 먼저 알린다.
3. Phase 0 구현 계획을 짧게 제시한다.
4. repository bootstrap을 실제로 수행한다.
5. Web/API/PostgreSQL/Redis local 실행 구조를 만든다.
6. GET /health를 구현한다.
7. test/lint/typecheck를 실행한다.
8. README의 실행 명령을 실제 구조와 맞게 갱신한다.
9. TASKS.md에서 실제 완료한 Phase 0 항목만 체크한다.

중요 제약:
- 마이크로서비스를 만들지 마라.
- Kubernetes/Kafka/GraphQL/vector DB를 추가하지 마라.
- 실제 AI Provider 연동은 아직 하지 마라.
- 실제 Meta 연동도 하지 마라.
- secret을 생성하거나 commit하지 마라.
- dependency는 최소화하라.
- 기존 파일을 삭제/대규모 변경하기 전에 이유를 확인하라.
- 테스트를 실행하지 않았다면 통과했다고 말하지 마라.

완료 후 다음 형식으로 보고하라:
Done / Files changed / Verification / Remaining / Next.
```

---

## Phase 1 Prompt

```text
AGENTS.md와 관련 docs를 다시 확인하라.
이번 범위는 TASKS.md Phase 1 — Tenant Core만이다.

Organization / Membership / Brand / Competitor와 tenant authorization을 구현하라.
특히 cross-tenant access denial test를 release blocker로 취급하라.

Phase 2 기능인 Creative/AI Job은 아직 구현하지 마라.

migration, integration test, README/env 변경을 포함하고
실제 완료한 TASKS.md 항목만 체크하라.
```

---

## Phase 2 Prompt

```text
AGENTS.md와 docs를 다시 확인하라.
이번 범위는 TASKS.md Phase 2 — Creative Intelligence Foundation만이다.

실제 유료 AI API를 부르지 말고 FakeAIProvider로 end-to-end Job flow를 완성하라.

필수 Golden Path:
Creative 등록
→ analysis 요청
→ Job queued
→ Celery worker
→ FakeAIProvider
→ schema validation
→ CreativeAnalysis 저장
→ ApiUsage 저장
→ Job completed
→ API 조회

tenant isolation, retry/error handling, usage logging 테스트를 포함하라.
```

---

## 코드 리뷰용 Prompt

```text
현재 변경사항을 구현하지 말고 먼저 리뷰하라.

AGENTS.md와 docs를 기준으로 다음을 우선 확인해라:
1. tenant isolation 취약점
2. secret 노출
3. async job 중복/유실 가능성
4. AI usage logging 누락
5. migration 문제
6. API contract 불일치
7. 테스트가 실제 요구사항을 검증하는지
8. 불필요한 over-engineering

발견사항을 severity 순으로 파일/위치와 함께 제시한 뒤,
수정 가치가 높은 항목부터 최소 patch를 적용하라.
수정 후 관련 test/lint/typecheck를 실행하라.
```
