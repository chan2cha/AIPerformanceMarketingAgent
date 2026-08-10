# Implementation Tasks

## 사용법

- Codex는 한 번에 **현재 Phase만** 구현한다.
- 실제 완료한 항목만 `[x]`.
- Phase가 끝날 때 테스트 결과를 기록한다.
- Scope 밖 기능을 발견해도 즉시 구현하지 말고 Backlog에 추가한다.

---

# Phase 0 — Repository Bootstrap

## Goal
로컬에서 Web/API/Postgres/Redis를 실행할 수 있는 개발 골격.

### Tasks
- [x] root repository 구조 생성
- [x] `apps/web` Next.js + TypeScript 초기화
- [x] `backend` FastAPI 프로젝트 초기화
- [x] Python dependency management 설정
- [x] SQLAlchemy / Alembic 설정
- [x] Redis / Celery 기본 설정
- [x] `infra/docker-compose.yml` 작성
- [x] `.env.example` 실제 변수 목록으로 갱신
- [x] backend `GET /health`
- [x] frontend 기본 화면에서 API health 확인 가능
- [x] backend test framework 설정
- [x] frontend lint/typecheck 설정
- [x] root README에 local run 명령 추가

### Acceptance Criteria
- [x] PostgreSQL + Redis local 실행 가능
- [x] Backend 실행 가능
- [x] Frontend 실행 가능
- [x] `GET /health` → 200
- [x] backend test command 성공
- [x] frontend lint/typecheck 성공
- [x] `.env`/secret이 git에 없음

### Verification — 2026-08-10

- `docker compose -f infra/docker-compose.yml up -d --build --wait`: Web/API/Worker/PostgreSQL/Redis 실행 확인. 기존 host 3000 포트 점유로 `WEB_PORT=3001` 오버라이드 사용.
- `GET http://localhost:8000/health`: `200 {"status":"ok"}`.
- Frontend `npm run lint`, `npm run typecheck`, `npm run build`: 성공.
- Backend Docker development target `pytest`: 1 passed.
- Backend Docker development target `ruff check .`: 성공.

---

# Phase 1 — Tenant Core

## Goal
Organization 단위 B2B SaaS 데이터 구조 구축.

### Tasks
- [ ] User model
- [ ] Organization model
- [ ] Membership model
- [ ] Brand model
- [ ] Competitor model
- [ ] Alembic migration
- [ ] Auth adapter 인터페이스
- [ ] local/dev용 인증 전략 정의
- [ ] Supabase token verification 구조
- [ ] Organization create/read endpoint
- [ ] Brand CRUD 최소 endpoint
- [ ] Competitor create/list/delete endpoint
- [ ] tenant authorization helper/service
- [ ] API integration tests
- [ ] cross-tenant access denial tests

### Acceptance Criteria
- [ ] User A가 Organization A 생성 가능
- [ ] A에 Brand/Competitor 생성 가능
- [ ] User B가 A의 resource UUID를 알아도 접근 불가
- [ ] migration from clean DB 성공
- [ ] 모든 integration test 성공

---

# Phase 2 — Creative Intelligence Foundation

## Goal
Creative를 저장하고 AI 분석 Job을 요청할 수 있다.

### Tasks
- [ ] Creative model
- [ ] CreativeAsset model
- [ ] CreativeAnalysis model
- [ ] Job model
- [ ] ApiUsage model
- [ ] migrations
- [ ] Creative manual create/list/detail API
- [ ] Creative filter
- [ ] AIProvider interface
- [ ] FakeAIProvider
- [ ] AIRouter
- [ ] CreativeAnalysis Pydantic schema
- [ ] prompt version structure
- [ ] analysis Job endpoint
- [ ] Celery task
- [ ] Job status endpoint
- [ ] usage/cost recorder
- [ ] retry/error handling
- [ ] idempotency 기본 정책
- [ ] worker tests

### Acceptance Criteria
- [ ] Creative 등록 가능
- [ ] 분석 요청 시 즉시 Job ID 반환
- [ ] Worker가 Fake provider로 분석 완료
- [ ] CreativeAnalysis row 생성
- [ ] ApiUsage row 생성
- [ ] Job completed
- [ ] 실패 provider 시 failed/retry 정책 확인
- [ ] tenant isolation 유지

---

# Phase 3 — First Real AI Provider

## Goal
실제 AI Provider 하나를 연결해 Creative 분석.

### Tasks
- [ ] Provider 선택/config
- [ ] 실제 Provider adapter
- [ ] structured output validation
- [ ] timeout
- [ ] retryable error mapping
- [ ] rate-limit mapping
- [ ] usage parsing
- [ ] pricing config
- [ ] estimated cost 계산
- [ ] opt-in smoke test
- [ ] secret handling 문서화

### Acceptance Criteria
- [ ] 실제 Creative 1건 분석 가능
- [ ] 결과 schema validation 성공
- [ ] usage/cost 기록
- [ ] provider error가 사용자에게 raw secret/detail을 노출하지 않음

---

# Phase 4 — Minimal Product UI

## Goal
마케터가 Golden Path를 UI로 수행.

### Screens
- [ ] Login
- [ ] Organization selector
- [ ] Brand list/create
- [ ] Competitor list/create
- [ ] Creative library
- [ ] Creative detail
- [ ] Analyze button
- [ ] Job status
- [ ] Analysis result
- [ ] Usage summary

### Acceptance Criteria
- [ ] Golden Path를 curl 없이 완료
- [ ] loading/error/empty 상태 존재
- [ ] tenant switch 시 데이터 혼선 없음

---

# Phase 5 — Meta Performance Integration

**현재 Codex가 선행 구현하지 말 것.**

- [ ] Meta OAuth/connection 설계
- [ ] Ad Account
- [ ] Campaign/Ad sync
- [ ] Creative mapping
- [ ] AdPerformanceDaily
- [ ] scheduled sync
- [ ] historical backfill
- [ ] API quota/error handling

---

# Phase 6 — Recommendation

**Phase 5 데이터 확보 후.**

- [ ] recommendation schema
- [ ] competitor pattern aggregation
- [ ] own performance aggregation
- [ ] recommendation prompt/logic
- [ ] rationale
- [ ] recommendation history
- [ ] accepted/executed feedback

---

# Phase 7 — Credits / Billing

- [ ] credit ledger
- [ ] plan allowance
- [ ] cost soft/hard limits
- [ ] reservation/settlement
- [ ] overage
- [ ] billing provider

---

# Phase 8 — Creative Generation

- [ ] image provider
- [ ] video provider
- [ ] generation job
- [ ] asset storage
- [ ] generation credits
- [ ] draft/final workflow

---

# Backlog

- pgvector similarity search
- shared market Creative DB
- agency multi-brand UX
- TikTok integration
- Shopify revenue integration
- automated weekly report
- Slack/email delivery
- experiment tracking
