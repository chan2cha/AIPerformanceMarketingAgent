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
- [x] User model
- [x] Organization model
- [x] Membership model
- [x] Brand model
- [x] Competitor model
- [x] Alembic migration
- [x] Auth adapter 인터페이스
- [x] local/dev용 인증 전략 정의
- [x] Supabase token verification 구조
- [x] Organization create/read endpoint
- [x] Brand CRUD 최소 endpoint
- [x] Competitor create/list/delete endpoint
- [x] tenant authorization helper/service
- [x] API integration tests
- [x] cross-tenant access denial tests

### Acceptance Criteria
- [x] User A가 Organization A 생성 가능
- [x] A에 Brand/Competitor 생성 가능
- [x] User B가 A의 resource UUID를 알아도 접근 불가
- [x] migration from clean DB 성공
- [x] 모든 integration test 성공

### Verification — 2026-08-10

- Backend `pytest`: 11 passed. PostgreSQL clean migration, API integration, invalid payload, auth mode guard, API/DB cross-tenant isolation 포함.
- Backend `ruff check .`: 성공.
- `alembic check`: model metadata와 migration 차이 없음.
- Main local PostgreSQL `alembic current`: `20260810_0001 (head)`.
- Production stack: API/PostgreSQL/Redis/Web healthy, Worker ready, API/Worker non-root 실행.
- Runtime smoke: `GET /health` 200, 미인증 `GET /api/v1/me` 401 error model, Phase 1 OpenAPI route 7개, Web API health 정상.
- Frontend `npm run lint`, `npm run typecheck`, `npm run build`: 성공.

---

# Phase 2 — Creative Intelligence Foundation

## Goal
Creative를 저장하고 AI 분석 Job을 요청할 수 있다.

### Tasks
- [x] Creative model
- [x] CreativeAsset model
- [x] CreativeAnalysis model
- [x] Job model
- [x] ApiUsage model
- [x] migrations
- [x] Creative manual create/list/detail API
- [x] Creative filter
- [x] AIProvider interface
- [x] FakeAIProvider
- [x] AIRouter
- [x] CreativeAnalysis Pydantic schema
- [x] prompt version structure
- [x] analysis Job endpoint
- [x] Celery task
- [x] Job status endpoint
- [x] usage/cost recorder
- [x] retry/error handling
- [x] idempotency 기본 정책
- [x] worker tests

### Acceptance Criteria
- [x] Creative 등록 가능
- [x] 분석 요청 시 즉시 Job ID 반환
- [x] Worker가 Fake provider로 분석 완료
- [x] CreativeAnalysis row 생성
- [x] ApiUsage row 생성
- [x] Job completed
- [x] 실패 provider 시 failed/retry 정책 확인
- [x] tenant isolation 유지

### Verification — 2026-08-10

- Backend `pytest`: 19 passed. Celery task golden path, API/DB tenant isolation, invalid payload, retryable/permanent/schema error, usage/cost logging, idempotency 포함.
- Backend `ruff check .`: 성공. `alembic check`: model metadata와 migration 차이 없음.
- Clean test DB migration head: `20260810_0002`. Local development DB도 동일 migration 적용.
- Local production stack: Web/API/Worker/PostgreSQL/Redis healthy. API가 `queued` Job ID를 즉시 반환하고 Redis/Celery worker가 `FakeAIProvider`로 처리해 `completed`; CreativeAnalysis 및 ApiUsage row 저장 확인.
- Runtime usage smoke: provider `fake`, task `creative_analysis`, input/output units `47/120`, synthetic estimated cost `0.00002870 USD`.
- Frontend `npm run lint`, `npm run typecheck`, `npm run build`: 성공.

---

# Phase 3 — First Real AI Provider

## Goal
실제 AI Provider 하나를 연결해 Creative 분석.

### Tasks
- [x] Provider 선택/config
- [x] 실제 Provider adapter
- [x] structured output validation
- [x] timeout
- [x] retryable error mapping
- [x] rate-limit mapping
- [x] usage parsing
- [x] pricing config
- [x] estimated cost 계산
- [x] opt-in smoke test
- [x] secret handling 문서화

### Acceptance Criteria
- [ ] 실제 Creative 1건 분석 가능
- [ ] 결과 schema validation 성공
- [ ] usage/cost 기록
- [x] provider error가 사용자에게 raw secret/detail을 노출하지 않음

### Verification — 2026-08-10

- Backend offline `pytest`: 27 passed, 1 skipped. OpenAI Responses parse/usage, timeout/connection/rate-limit/4xx/5xx mapping, cached-token cost, sanitized Job error 포함.
- 유료 OpenAI smoke test는 `OPENAI_API_KEY` 부재 및 `RUN_OPENAI_SMOKE` 비활성으로 실행하지 않음.
- Backend `ruff check .`: 성공. `alembic check`: model metadata와 migration 차이 없음.
- OpenAI 가격 config: `gpt-5.6-luna` input/cached/output token 단가와 model snapshot fallback 검증.
- Local migration head `20260810_0003`; Web/API/Worker/PostgreSQL/Redis production stack healthy.
- 기본 `AI_PROVIDER=fake` Redis/Celery 회귀: API `queued`, Worker `completed`, prompt `creative-analysis-v2` 저장 확인.
- Frontend `npm run lint`, `npm run typecheck`, `npm run build`: 성공.

---

# Phase 4 — Minimal Product UI

## Goal
마케터가 Golden Path를 UI로 수행.

### Screens
- [x] Login
- [x] Organization selector
- [x] Brand list/create
- [x] Competitor list/create
- [x] Creative library
- [x] Creative detail
- [x] Analyze button
- [x] Job status
- [x] Analysis result
- [x] Usage summary

### Acceptance Criteria
- [x] Golden Path를 curl 없이 완료
- [x] loading/error/empty 상태 존재
- [x] tenant switch 시 데이터 혼선 없음

### Verification — 2026-08-10

- Web operational workspace에서 local dev login, Organization/Brand/Competitor 생성, Creative 등록/필터/상세, 분석 요청과 Job polling, 구조화 결과, tenant usage summary 흐름 구현.
- Organization 전환 시 tenant-owned UI state를 요청 전에 초기화하고 이전 비동기 응답을 version guard로 폐기. Backend usage endpoint를 포함한 cross-tenant 접근은 404로 검증.
- Backend `pytest`: 27 passed, 1 skipped(OpenAI 유료 opt-in smoke). usage aggregation/invalid period/tenant denial과 기존 Golden Path 포함.
- Backend `ruff check .`: 성공. `alembic check`: model metadata와 migration 차이 없음.
- Frontend `npm run lint`, `npm run typecheck`, `npm run build`: 성공. `WEB_BASE_URL=http://localhost:3001 npm run test:smoke`: 성공.
- Docker production stack: Web/API/Worker/PostgreSQL/Redis 기동 확인. `GET /health` 200, Web origin CORS preflight 200.

---

# Phase 5 — Automated Market Intelligence

## Goal
브랜드·업종·경쟁사를 설정하면 Script 생성에 필요한 시장 광고를 자동 수집·분석한다.

### Tasks
- [x] CollectionSource model/migration
- [x] provider-independent AdLibraryCollector interface/router
- [x] deterministic Fake Collector
- [x] 브랜드별 수집 소스 create/list API
- [x] 비동기 market content sync Job/Worker
- [x] 외부 ID 기반 Creative 중복 방지
- [x] 신규 Creative 자동 분석 Job 연결
- [x] invalid payload test
- [x] tenant isolation test
- [x] job state transition/idempotency test
- [ ] 베트남 Meta 상업 광고 production provider 확정 및 adapter
- [ ] 베트남 TikTok 광고 production provider 확정 및 adapter
- [x] 주기적 scheduled sync
- [x] source pause/resume 및 sync health UI
- [x] 브랜드 → 시장 → 자동 수집 → 분석 스텝퍼 UI
- [ ] OCR/영상 자막·음성 추출
- [ ] 경쟁사·업종별 pattern aggregation

### Acceptance Criteria
- [x] 경쟁사 또는 업종 단위 수집 소스 설정 가능
- [x] API가 sync Job ID를 즉시 반환
- [x] Worker가 Fake Collector로 신규 Creative를 수집
- [x] 동일 외부 광고 재수집 시 중복 Creative가 생기지 않음
- [x] 신규 Creative 분석 Job 생성
- [x] 다른 Organization의 competitor/source에 접근 불가
- [ ] production provider로 베트남 광고 1건 이상 수집
- [x] 정기 sync와 source별 운영 상태 확인 가능

### Verification — 2026-08-21

- Backend `pytest`: 31 passed, 1 skipped(OpenAI 유료 opt-in smoke). 자동 수집 golden path, scheduler due/paused 처리, invalid payload, cross-tenant source 차단, Job 성공·실패 상태 전이, 외부 ID 중복 방지, 신규 Creative 분석 Job 연결 포함.
- Backend `ruff check .`: 성공. `alembic check`: model metadata와 migration 차이 없음.
- Clean test DB migration head 및 local DB: `20260821_0005`.
- Frontend `npm run lint`, `npm run typecheck`, `npm run build`: 성공.
- 한 화면에 혼재하던 설정·수집·분석 UI를 4단계 작업 화면으로 분리하고, 단계별 완료 상태와 이전/다음 이동을 제공.
- Docker production stack Web/API/Worker/Scheduler/PostgreSQL/Redis 기동, `GET /health` 200, Web smoke 성공.
- Runtime Fake Collector smoke: 베트남 Meta 수집 소스 → sync completed → Creative 1건 → 자동 AI 분석 1건 완료.
- Runtime scheduler smoke: due source 2건 enqueue → TikTok 베트남 Creative 1건 수집 → 자동 분석 1건 완료 → 다음 실행 시각 24시간 후 갱신.
- 실제 Meta/TikTok 광고를 수집한 것이 아니며 production provider adapter는 미완료.

---

# Phase 6 — Meta Performance Integration

- [ ] Meta OAuth/connection 설계
- [ ] Ad Account
- [ ] Campaign/Ad sync
- [ ] Creative mapping
- [ ] AdPerformanceDaily
- [ ] scheduled sync
- [ ] historical backfill
- [ ] API quota/error handling

---

# Phase 7 — Recommendation

**Phase 5~6 데이터 확보 후.**

- [ ] recommendation schema
- [ ] competitor pattern aggregation
- [ ] own performance aggregation
- [ ] recommendation prompt/logic
- [ ] rationale
- [ ] recommendation history
- [ ] accepted/executed feedback

---

# Phase 8 — Credits / Billing

- [ ] credit ledger
- [ ] plan allowance
- [ ] cost soft/hard limits
- [ ] reservation/settlement
- [ ] overage
- [ ] billing provider

---

# Phase 9 — Creative Generation

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
- shared market-level pattern aggregation
- Shopify revenue integration
- automated weekly report
- Slack/email delivery
- experiment tracking
