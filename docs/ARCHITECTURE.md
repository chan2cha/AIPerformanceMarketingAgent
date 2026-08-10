# Architecture

## 1. 목표

MVP는 **Modular Monolith + Asynchronous Worker** 구조로 만든다.

이유:
- 제품 요구사항이 아직 변한다.
- AI/광고 연동은 비동기 작업이 많다.
- 서비스 분리 비용보다 빠른 학습이 중요하다.
- 이후 실제 병목에 따라 Worker 또는 특정 integration만 분리할 수 있다.

## 2. High-level Architecture

```text
                     Browser
                       │
                       ▼
              ┌─────────────────┐
              │ Next.js Web App │
              │   TypeScript    │
              └────────┬────────┘
                       │ HTTPS
                       ▼
              ┌─────────────────┐
              │ FastAPI Backend │
              │     Python      │
              └───┬─────────┬───┘
                  │         │
          sync DB │         │ enqueue
                  ▼         ▼
            PostgreSQL    Redis
                              │
                              ▼
                      ┌───────────────┐
                      │ Celery Worker │
                      └───────┬───────┘
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
           AI Providers   Ad Providers     Storage
           OpenAI/...     Meta/...         Supabase/S3
```

## 3. Repository Layout

```text
/
├── AGENTS.md
├── README.md
├── TASKS.md
├── CODEX_START.md
├── apps/
│   └── web/
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── lib/
│       └── tests/
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── modules/
│   │   │   ├── organizations/
│   │   │   ├── brands/
│   │   │   ├── competitors/
│   │   │   ├── creatives/
│   │   │   ├── jobs/
│   │   │   ├── usage/
│   │   │   └── recommendations/
│   │   ├── ai/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── prompts/
│   │   │   └── providers/
│   │   └── integrations/
│   ├── worker/
│   │   ├── celery_app.py
│   │   └── tasks/
│   └── tests/
├── infra/
│   └── docker-compose.yml
└── docs/
```

FastAPI와 Celery Worker는 **동일한 Python domain/package를 공유**한다.

## 4. Backend Module Rule

각 module은 필요에 따라 대략 아래 책임을 가진다.

```text
modules/creatives/
├── router.py       # HTTP
├── schemas.py      # request/response DTO
├── service.py      # use cases
├── repository.py   # persistence
└── domain.py       # 필요 시 domain types
```

초기에는 폴더를 기계적으로 모두 만들지 않는다. Router에서 DB query와 AI SDK 호출을 직접 섞지 않는다.

## 5. Creative Analysis Request / Job Flow

```text
POST /v1/creatives/{id}/analyses
        │
        ▼
권한/tenant 검증
        │
        ▼
Job row 생성 (queued)
        │
        ▼
Celery enqueue
        │
        ▼
HTTP 202 + job_id
```

Worker:

```text
Job queued
   ↓
processing
   ↓
Creative + asset 데이터 로드
   ↓
AIRouter
   ↓
Provider
   ↓
Schema validation
   ↓
creative_analysis 저장
   ↓
api_usage 저장
   ↓
Job completed
```

실패는 retryable 여부에 따라 재시도 후 `failed`로 기록하며 사용자에게는 sanitized error만 노출한다.

## 6. AI Provider Abstraction

도메인은 공급자를 몰라야 한다.

개념 인터페이스:

```python
class AIProvider(Protocol):
    async def analyze_creative(
        self,
        request: CreativeAnalysisRequest,
    ) -> ProviderResult[CreativeAnalysisResult]:
        ...
```

`ProviderResult`에는 최소 아래가 필요하다.
- output
- provider
- model
- input/output usage
- request id 가능 시
- latency
- raw metadata 최소 범위

`AIRouter`는 task/config에 따라 provider/model을 선택한다.
MVP에서는 실제 provider 하나만 구현해도 abstraction은 유지한다.

## 7. Auth

권장 흐름:
- Frontend: Supabase Auth
- Frontend → API: access token 전달
- Backend: JWT 검증
- Backend: authenticated user와 membership 조회
- organization scope 확정 후 query

**Frontend가 보낸 organization_id를 신뢰하지 않는다.**

## 8. Storage

Media binary를 PostgreSQL에 저장하지 않는다.

```text
PostgreSQL
- asset metadata
- object key
- content type
- size/checksum

Object Storage
- actual image/video/file
```

Private bucket 기본. 필요 시 signed URL 발급.

## 9. PostgreSQL 사용 원칙

정규 컬럼:
- organization_id
- creative type
- hook_type
- offer_type
- status
- date
- spend/roas

JSONB:
- raw_payload
- provider_metadata

핵심 비즈니스 필드를 전부 JSONB에 넣지 않는다.

## 10. Redis/Caching

MVP에서는 Redis를 주로 Celery broker/backend 용도로 사용한다.
캐시는 실제 필요성이 확인된 후 추가한다.
경쟁사 Creative 분석 결과는 캐시보다 DB의 재사용 가능한 구조화 데이터로 저장하는 것을 우선한다.

## 11. Observability

최소 로그 필드:
- timestamp
- environment
- request_id
- job_id
- organization_id
- user_id
- module
- severity
- error_code

AI 추가:
- provider
- model
- task
- latency
- usage
- estimated_cost

Secret이나 전체 prompt/raw customer data를 무조건 로그에 남기지 않는다.

## 12. 확장 시 분리 후보

실제 병목이 측정되기 전까지 분리하지 않는다.
- Data ingestion worker
- Media generation worker
- Recommendation service

현재는 하나의 backend codebase에서 처리한다.
