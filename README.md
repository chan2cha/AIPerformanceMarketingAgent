# AI Performance Marketing SaaS

B2B 커머스 팀의 광고 관찰·분석 흐름을 연결하는 MVP입니다. 현재 Phase 5 Automated Market Intelligence 기반까지 구현되어 Organization 단위 데이터 격리, Brand/Competitor 관리, 광고 수집 소스 설정, 비동기 수집·분석 Job과 usage summary를 브라우저에서 사용할 수 있습니다. 기본값은 네트워크나 비용이 없는 deterministic `FakeAdLibraryCollector`와 `FakeAIProvider`이며, 실제 광고 라이브러리 adapter는 승인된 production 데이터 공급자가 확정된 후 연결합니다.

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
docker compose -f infra/docker-compose.yml up -d postgres redis
docker compose -f infra/docker-compose.yml run --build --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml up --build -d --wait
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
3. `자동 수집` 화면에서 Meta/TikTok, 경쟁사·업종, 국가·언어와 자동 수집 주기를 지정합니다.
4. scheduler가 주기적으로 수집하며, 필요하면 `지금 수집`으로 즉시 실행하거나 일시중지할 수 있습니다.
5. `분석` 화면에서 수집 광고와 구조화 분석 결과를 확인합니다. 자동 수집에서 누락된 광고만 `직접 추가`로 보완합니다.
6. 같은 분석 화면에서 Organization별 AI 호출 수와 추정 비용을 확인합니다.

조직 선택을 바꾸면 기존 Brand, Competitor, Creative, 분석, Job, usage 상태를 즉시 비운 뒤 새 tenant 데이터를 요청합니다. API도 membership을 재검증합니다. 현재 로그인 화면은 `AUTH_MODE=dev` local 환경용이며 Supabase production 로그인 UI는 Phase 4 범위에 포함하지 않습니다.

Web과 API를 다른 origin으로 실행하므로 `CORS_ORIGINS`에 허용할 Web origin을 쉼표로 구분해 지정합니다. local 기본값은 `http://localhost:3000,http://localhost:3001`입니다.

광고 라이브러리 수집은 local/test에서 기본적으로 synthetic 광고 1건을 반환하는 Fake Collector를 사용합니다. 실제 Meta/TikTok 데이터를 수집한다고 오해하지 않도록 production adapter가 준비되지 않은 환경에서는 `AD_LIBRARY_PROVIDER=disabled`로 설정합니다.

```dotenv
AD_LIBRARY_PROVIDER=fake
COLLECTION_JOB_MAX_RETRIES=2
COLLECTION_JOB_RETRY_DELAY_SECONDS=5
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
$env:RUN_OPENAI_SMOKE="1"
docker compose -f infra/docker-compose.yml --profile test run --rm -e RUN_OPENAI_SMOKE=1 -e OPENAI_API_KEY backend-test pytest -m openai_smoke
```

OpenAI 가격은 [공식 GPT-5.6 Luna 모델 페이지](https://developers.openai.com/api/docs/models/gpt-5.6-luna)를 기준으로 `backend/app/ai/pricing.json`에 날짜별로 검토 가능한 config로 분리합니다. 가격 변경 시 코드를 수정하지 않고 config와 검증 기대값을 함께 갱신합니다.

포트가 이미 사용 중이면 해당 세션에서 오버라이드할 수 있습니다.

```powershell
$env:WEB_PORT="3001"
docker compose -f infra/docker-compose.yml up -d --wait
```

컨테이너를 중지하되 PostgreSQL named volume은 보존합니다.

```powershell
docker compose -f infra/docker-compose.yml down
```

## 검증 명령

Backend test와 lint는 host Python 설치 없이 development image에서 실행할 수 있습니다.

```powershell
docker compose -f infra/docker-compose.yml --profile test run --build --rm backend-test
docker compose -f infra/docker-compose.yml --profile test run --rm backend-test ruff check .
docker compose -f infra/docker-compose.yml --profile test run --rm backend-test alembic check
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
docker compose -f infra/docker-compose.yml up -d postgres redis
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
