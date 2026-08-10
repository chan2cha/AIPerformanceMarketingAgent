# AI Performance Marketing SaaS

B2B 커머스 팀의 광고 관찰·분석·추천 흐름을 연결하는 MVP입니다. 현재 구현 범위는 Phase 0 개발 골격이며, 실제 인증·고객 데이터 모델·AI Provider·Meta 연동은 포함하지 않습니다.

## 구조

- `apps/web`: Next.js 16 / React 19 / TypeScript frontend
- `backend/app`: FastAPI modular monolith
- `backend/worker`: backend package를 공유하는 Celery worker
- `backend/alembic`: SQLAlchemy/Alembic migration 기반
- `infra/docker-compose.yml`: Web, API, Worker, PostgreSQL, Redis local stack
- `docs`: 제품·아키텍처·데이터·API 문서

## 사전 요구사항

- Docker Desktop과 Docker Compose
- frontend를 호스트에서 실행하려면 Node.js 24+와 npm 11+
- backend를 호스트에서 실행하려면 Python 3.12+

## 전체 local stack 실행

프로젝트 루트에서 실행합니다. `.env` 없이도 공개된 local development 기본값으로 기동하며, 값을 바꿔야 할 때만 `.env.example`을 `.env`로 복사합니다. `.env`는 Git에서 제외됩니다.

```powershell
docker compose -f infra/docker-compose.yml up --build -d --wait
```

기본 주소:

- Web: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

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
```

Frontend 의존성과 정적 검사를 실행합니다.

```powershell
cd apps/web
npm install
npm run lint
npm run typecheck
npm run build
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
uvicorn app.main:app --reload
```

다른 터미널에서 Web을 실행합니다.

```powershell
cd apps/web
npm install
npm run dev
```

자세한 요구사항과 다음 Phase는 [TASKS.md](TASKS.md), [Architecture](docs/ARCHITECTURE.md), [Testing Strategy](docs/TESTING.md)를 참고합니다.
