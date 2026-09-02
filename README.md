# AI Performance Marketing SaaS

B2B 커머스 팀의 광고 관찰·분석 흐름을 연결하는 MVP입니다. 현재 Phase 5 Automated Market Intelligence 기반까지 구현되어 Organization 단위 데이터 격리, Brand/Competitor 관리, Meta·TikTok 광고 수집 소스 설정, 비동기 수집·분석 Job과 usage summary를 브라우저에서 사용할 수 있습니다. 기본값은 네트워크나 비용이 없는 deterministic `FakeAdLibraryCollector`와 `FakeAIProvider`입니다.

## 구조

- `apps/web`: Next.js 16 / React 19 / TypeScript frontend
- `backend/app`: FastAPI modular monolith
- `backend/app/modules`: Tenant Core, Creative, Ingestion, Job, Usage domain modules
- `backend/app/integrations`: provider-independent 광고 라이브러리 collector
- `backend/app/ai`: provider interface, router, FakeAIProvider, versioned prompt/schema, pricing config
- `backend/worker`: backend package를 공유하는 Celery worker
- `scheduler`: due 수집 소스를 5분마다 확인하는 Celery Beat process
- `backend/alembic`: SQLAlchemy/Alembic migration 기반
- `infra/docker-compose.yml`: Web, API, Worker, PostgreSQL, Redis local stack
- `docs`: 제품·아키텍처·데이터·API 문서

## 사전 요구사항

- Docker Desktop과 Docker Compose
- frontend를 호스트에서 실행하려면 Node.js 24+와 npm 11+
- backend를 호스트에서 실행하려면 Python 3.12+

## 전체 local stack 실행

프로젝트 루트에서 실행합니다. `.env` 없이도 공개된 local development 기본값으로 기동하며, 값을 바꿔야 할 때만 `.env.example`을 `.env`로 복사합니다. `.env`는 Git에서 제외됩니다.

PostgreSQL을 먼저 실행하고 migration을 적용한 뒤 전체 stack을 시작합니다.

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d postgres redis
docker compose --env-file .env -f infra/docker-compose.yml run --build --rm api alembic upgrade head
docker compose --env-file .env -f infra/docker-compose.yml up --build -d --wait
```

기본 주소:

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## 인증

Local 환경의 기본값은 deterministic dev auth입니다. Bearer token의 subject가 내부 `users.auth_user_id`와 연결됩니다.

```text
Authorization: Bearer dev:<subject>
```

예시:

```powershell
$headers = @{ Authorization = "Bearer dev:owner-a" }
$body = @{ name = "Brand Company" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/organizations -Headers $headers -ContentType "application/json" -Body $body
```

`AUTH_MODE=dev`는 `APP_ENV=production`에서 거부됩니다. Supabase Auth를 사용할 때는 다음 공개 설정을 지정합니다. Backend는 access token의 공개 JWKS 서명, issuer, audience, 만료를 검증하며 service-role key를 사용하지 않습니다.

```dotenv
APP_ENV=production
AUTH_MODE=supabase
SUPABASE_URL=https://project-ref.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
```

## $40 구독과 운영 Provider 설정

사용자는 Web의 첫 번째 `플랜` 단계에서 Organization 단위로 월 `$40` 플랜을 결제합니다. 결제가 활성화되면 월 provider credit `$15`, AI 분석 200회, 자동 수집 50회, 브랜드 1개, 경쟁 브랜드 5개 한도가 적용됩니다. 비용이 발생하는 Job은 실행 전에 credit을 예약하고 성공 시 실제 또는 보수적 추정 비용으로 확정하며, 실패하면 예약을 반환합니다.

사용자가 Web에서 입력하는 정보는 다음뿐입니다.

- 회사/팀 이름: `플랜` 또는 `브랜드` 단계
- 브랜드 이름과 업종: `브랜드` 단계
- 경쟁 브랜드 이름과 웹사이트: `시장` 단계
- 플랫폼, 국가, 언어, 경쟁사 또는 검색어, 주기: `자동 수집` 단계

Apify token, OpenAI key, Stripe secret은 사용자 화면에 입력하지 않습니다. local에서는 Git에 포함되지 않는 root `.env`, production에서는 배포 환경의 secret manager에 입력합니다. `NEXT_PUBLIC_*` 변수나 frontend bundle에는 절대 넣지 않습니다.

### 1. Stripe

Stripe Dashboard에서 월 `$40 USD` recurring Product/Price를 하나 만들고 다음 값을 설정합니다. 운영 API에만 주입합니다.

```dotenv
APP_ENV=production
BILLING_PROVIDER=stripe
BILLING_ENFORCEMENT_ENABLED=true
BILLING_MONTHLY_PRICE_USD=40.00
BILLING_MONTHLY_CREDIT_USD=15.00
STRIPE_SECRET_KEY=<Stripe secret key>
STRIPE_PRICE_ID=<월 40 USD recurring price id>
STRIPE_WEBHOOK_SECRET=<webhook signing secret>
BILLING_SUCCESS_URL=https://<web-domain>/?billing=success
BILLING_CANCEL_URL=https://<web-domain>/?billing=cancelled
```

Stripe webhook endpoint는 `https://<api-domain>/api/v1/billing/webhooks/stripe`이며 다음 event를 전달합니다.

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

local 기본값 `BILLING_PROVIDER=fake`는 카드를 청구하지 않고 플랜을 즉시 활성화합니다. production에서는 fake billing과 enforcement 비활성 상태로 API가 시작되지 않습니다.

### 2. Apify

Apify 약관과 월 예산을 승인한 뒤 API token을 production Worker에만 주입합니다. 현재 플랫폼별 실행 상한은 `$0.25`, 결과 상한은 25건입니다.

```dotenv
AD_LIBRARY_PROVIDER=apify
APIFY_API_TOKEN=<Apify API token>
APIFY_META_ACTOR_ID=apify~facebook-ads-scraper
APIFY_TIKTOK_ACTOR_ID=khadinakbar~tiktok-ads-scraper
APIFY_META_MAX_ITEMS_PER_SYNC=25
APIFY_META_MAX_CHARGE_USD_PER_SYNC=0.25
APIFY_MAX_ITEMS_PER_SYNC=25
APIFY_MAX_CHARGE_USD_PER_SYNC=0.25
APIFY_TIKTOK_PERIOD_DAYS=30
APIFY_CONFIGURED=true
```

`APIFY_API_TOKEN`은 Worker 전용 secret이고, `APIFY_CONFIGURED=true`는 API가 Web에 secret 없이 연결 상태만 알리기 위한 비민감 플래그입니다.

### 3. OpenAI

OpenAI project에서 Worker용 API key를 발급해 production Worker에만 주입합니다.

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=<OpenAI project API key>
OPENAI_MODEL=gpt-5.6-luna
OPENAI_TIMEOUT_SECONDS=30
OPENAI_CONFIGURED=true
```

`OPENAI_API_KEY`는 Worker 전용이고, `OPENAI_CONFIGURED=true`는 Web의 연결 상태 표시용 비민감 플래그입니다.

현재 주요 endpoint:

- `GET /api/v1/me`
- `POST/GET /api/v1/organizations...`
- `POST/GET/PATCH /api/v1/.../brands...`
- `POST/GET/DELETE /api/v1/.../competitors...`
- `POST/GET /api/v1/brands/{brand_id}/collection-sources`
- `POST /api/v1/collection-sources/{source_id}/sync`
- `POST/GET /api/v1/brands/{brand_id}/creatives`
- `GET /api/v1/creatives/{creative_id}`
- `POST/GET /api/v1/creatives/{creative_id}/analyses`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/organizations/{organization_id}/usage`

Organization-owned endpoint는 모두 인증과 membership 검증이 필요합니다. 다른 tenant의 UUID를 직접 사용해도 일관되게 404를 반환합니다.

## Phase 5 Web UI

Web 주소를 열고 local development account에 임의의 subject(기본값 `demo-owner`)를 입력합니다. 첫 접속이라면 Organization과 Brand를 차례로 만든 후 다음 흐름을 UI에서 수행할 수 있습니다.

Web 작업 공간은 `브랜드 → 시장 → 자동 수집 → 분석` 4단계 스텝퍼로 구성됩니다.

1. `브랜드` 화면에서 회사/팀과 분석 기준 브랜드를 선택하거나 만듭니다.
2. `시장` 화면에서 베트남 시장에서 비교할 경쟁 브랜드를 등록합니다. 경쟁사 없이 업종 키워드만으로도 다음 단계로 진행할 수 있습니다.
3. `시장 광고 조사` 화면에서 Meta 또는 TikTok, 경쟁사·업종, 국가·언어와 자동 수집 주기를 지정합니다. 각 공식 라이브러리 링크에서 원본도 확인할 수 있습니다.
4. scheduler가 주기적으로 수집하며, 필요하면 `지금 수집`으로 즉시 실행하거나 일시중지할 수 있습니다.
5. `분석` 화면에서 수집 광고와 구조화 분석 결과를 확인합니다. 자동 수집에서 누락된 광고만 `직접 추가`로 보완합니다.
6. 같은 분석 화면에서 Organization별 AI 호출 수와 추정 비용을 확인합니다.

조직 선택을 바꾸면 기존 Brand, Competitor, Creative, 분석, Job, usage 상태를 즉시 비운 뒤 새 tenant 데이터를 요청합니다. API도 membership을 재검증합니다. 현재 로그인 화면은 `AUTH_MODE=dev` local 환경용이며 Supabase production 로그인 UI는 Phase 4 범위에 포함하지 않습니다.

Web과 API를 다른 origin으로 실행하므로 `CORS_ORIGINS`에 허용할 Web origin을 쉼표로 구분해 지정합니다. local 기본값은 `http://localhost:3000,http://localhost:3001`입니다.

광고 라이브러리 수집은 local/test에서 synthetic 광고를 반환하는 Fake Collector를 사용합니다. production 설정은 Meta에 Apify 공식 유지보수 Facebook Ads Library Actor를, TikTok에 Creative Center Top Ads Actor를 사용합니다. Meta는 공개 웹 광고 자료라 누락·구조 변경 가능성이 있고, TikTok은 경쟁사의 전체 광고가 아닌 공개 인기 광고 표본입니다. 실제 운영 전에는 약관·예산 승인과 베트남 유료 smoke가 필요합니다.

```dotenv
AD_LIBRARY_PROVIDER=fake
COLLECTION_JOB_MAX_RETRIES=2
COLLECTION_JOB_RETRY_DELAY_SECONDS=5
```

승인 후 실제 Worker에만 Apify token을 주입한다. API/Web/Scheduler에는 token을 전달하지 않는다. 호출당 수집 건수와 최대 과금을 동시에 제한한다.

```dotenv
AD_LIBRARY_PROVIDER=apify
APIFY_API_TOKEN=<worker-only-secret>
APIFY_META_ACTOR_ID=apify~facebook-ads-scraper
APIFY_META_MAX_ITEMS_PER_SYNC=25
APIFY_META_MAX_CHARGE_USD_PER_SYNC=0.25
APIFY_TIKTOK_ACTOR_ID=khadinakbar~tiktok-ads-scraper
APIFY_MAX_ITEMS_PER_SYNC=25
APIFY_MAX_CHARGE_USD_PER_SYNC=0.25
APIFY_TIKTOK_PERIOD_DAYS=30
```

실제 베트남 광고 smoke는 비용이 발생하므로 명시적으로 실행한다.

```powershell
docker compose --env-file .env -f infra/docker-compose.yml --profile test run --rm -e RUN_APIFY_SMOKE=1 backend-test pytest -m apify_smoke
```

## Phase 2 Creative 분석 Golden Path

먼저 위 인증 예시처럼 Organization과 Brand를 만들고 반환된 ID를 사용합니다. 아래 분석 요청은 Job을 queue에 넣고 즉시 `202`와 Job ID를 반환합니다. 같은 Creative의 기본 요청은 현재 prompt version 단위로 idempotent하며, 새 분석이 필요할 때만 `force=true`를 사용합니다.

```powershell
$headers = @{ Authorization = "Bearer dev:owner-a" }
$creativeBody = @{
  ownership_type = "own"
  media_type = "image"
  title = "여름 스킨케어 캠페인"
  body = "가볍고 산뜻한 수분 케어"
} | ConvertTo-Json
$creative = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/brands/$brandId/creatives" -Headers $headers -ContentType "application/json" -Body $creativeBody

$analysisBody = @{ force = $false } | ConvertTo-Json
$accepted = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/creatives/$($creative.id)/analyses" -Headers $headers -ContentType "application/json" -Body $analysisBody
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/jobs/$($accepted.job_id)" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/creatives/$($creative.id)" -Headers $headers
```

Worker는 `queued → processing → completed`로 Job을 갱신하고, schema validation을 통과한 `CreativeAnalysis`와 provider/model/task/units/추정 비용을 담은 `ApiUsage`를 같은 DB 작업으로 저장합니다. Fake provider의 단가는 실제 공급자 가격이 아닌 비용 계산 검증용 synthetic config입니다.

## Phase 3 OpenAI provider (opt-in)

첫 실제 provider는 OpenAI Responses API, 기본 모델은 `gpt-5.6-luna`입니다. OpenAI adapter는 Pydantic structured output을 사용하고 input/cached input/output token과 request ID를 기록합니다. timeout, 연결 실패, rate limit, 5xx는 Celery retry 대상으로 분류하며 그 밖의 provider 오류는 sanitized failed Job으로 기록합니다.

기본 local stack과 CI는 계속 `AI_PROVIDER=fake`를 사용합니다. 실제 provider를 사용할 Worker에만 다음 값을 주입합니다.

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=<secret-manager-or-local-untracked-value>
OPENAI_MODEL=gpt-5.6-luna
OPENAI_TIMEOUT_SECONDS=30
```

Secret 처리 원칙:

- `OPENAI_API_KEY`를 commit하거나 `NEXT_PUBLIC_*` 변수로 만들지 않습니다.
- local에서만 Git ignored `.env` 또는 현재 process environment를 사용합니다.
- production에서는 배포 환경의 secret manager에서 Worker에만 주입합니다.
- key, SDK exception 원문, provider response 전체를 Job error/API response에 기록하지 않습니다.
- 유출이 의심되면 provider console에서 즉시 key를 폐기하고 교체합니다.

실제 비용이 발생하는 smoke test는 두 opt-in 조건을 모두 만족할 때만 실행됩니다. `OPENAI_API_KEY`는 명령 인자에 값을 직접 쓰지 말고 현재 shell 환경에 미리 주입합니다.

```powershell
docker compose --env-file .env -f infra/docker-compose.yml --profile test run --rm -e RUN_OPENAI_SMOKE=1 backend-test pytest -m openai_smoke
```

OpenAI 가격은 [공식 GPT-5.6 Luna 모델 페이지](https://developers.openai.com/api/docs/models/gpt-5.6-luna)를 기준으로 `backend/app/ai/pricing.json`에 날짜별로 검토 가능한 config로 분리합니다. 가격 변경 시 코드를 수정하지 않고 config와 검증 기대값을 함께 갱신합니다.

포트가 이미 사용 중이면 해당 세션에서 오버라이드할 수 있습니다.

```powershell
$env:WEB_PORT="3001"
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
```

컨테이너를 중지하되 PostgreSQL named volume은 보존합니다.

```powershell
docker compose --env-file .env -f infra/docker-compose.yml down
```

## 검증 명령

Backend test와 lint는 host Python 설치 없이 development image에서 실행할 수 있습니다.

```powershell
docker compose --env-file .env -f infra/docker-compose.yml --profile test run --build --rm backend-test
docker compose --env-file .env -f infra/docker-compose.yml --profile test run --rm backend-test ruff check .
docker compose --env-file .env -f infra/docker-compose.yml --profile test run --rm backend-test alembic check
```

Integration test는 별도 `performance_marketing_test` PostgreSQL database를 만들고 빈 schema에 migration을 적용합니다. 안전을 위해 database 이름이 `_test`로 끝나지 않으면 schema 초기화를 거부합니다.

Frontend 의존성과 정적 검사를 실행합니다.

```powershell
cd apps/web
npm install
npm run lint
npm run typecheck
npm run build
npm run test:smoke
```

Web을 3001 포트로 실행했다면 smoke 대상도 맞춥니다.

```powershell
$env:WEB_BASE_URL="http://localhost:3001"
npm run test:smoke
```

Health를 직접 확인합니다.

```powershell
Invoke-RestMethod http://localhost:8000/health
```

예상 응답:

```json
{"status":"ok"}
```

## Host 개발 실행 (선택)

Docker로 PostgreSQL과 Redis를 먼저 실행합니다.

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d postgres redis
```

Python 3.12+ 환경에서 API를 실행합니다.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

다른 터미널에서 Web을 실행합니다.

```powershell
cd apps/web
npm install
npm run dev
```

자세한 요구사항과 다음 Phase는 [TASKS.md](TASKS.md), [Architecture](docs/ARCHITECTURE.md), [Testing Strategy](docs/TESTING.md)를 참고합니다.
