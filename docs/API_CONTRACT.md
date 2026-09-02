# API Contract — MVP

Base path: `/api/v1`

모든 Organization-owned route는 인증을 요구한다.

## 1. Health

### GET `/health`

Response `200`

```json
{"status":"ok"}
```

가능하면 DB/Redis readiness와 단순 process liveness를 분리한다.

## 2. Me

### GET `/api/v1/me`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "홍길동",
  "organizations": [
    {"id":"uuid","name":"Brand Company","role":"owner"}
  ]
}
```

## 3. Organizations

### POST `/api/v1/organizations`

```json
{"name":"Brand Company"}
```

Behavior:
- Organization 생성
- 요청 사용자를 owner membership으로 추가
- 하나의 transaction으로 처리

Response `201`

### GET `/api/v1/organizations/{organization_id}`
Membership 필요.

## 4. Brands

### POST `/api/v1/organizations/{organization_id}/brands`

```json
{
  "name":"Example Beauty",
  "website":"https://example.com",
  "industry":"beauty",
  "description":"스킨케어 브랜드",
  "target_customer":"20~35세 여성"
}
```

### GET `/api/v1/organizations/{organization_id}/brands`
Pagination 고려.

### GET `/api/v1/brands/{brand_id}`
Backend가 brand의 organization과 requester membership을 확인한다.

### PATCH `/api/v1/brands/{brand_id}`
Partial update.

## 5. Competitors

### POST `/api/v1/brands/{brand_id}/competitors`

```json
{
  "name":"Competitor A",
  "website":"https://competitor.example",
  "instagram_url":null,
  "meta_page_id":null,
  "tiktok_url":null
}
```

### GET `/api/v1/brands/{brand_id}/competitors`

### DELETE `/api/v1/competitors/{competitor_id}`
Phase 1에서는 관련 Creative가 아직 없으므로 hard delete한다. Phase 2에서 Creative FK를 추가하기 전에 삭제 정책을 다시 결정한다.

## 6. Creatives

### POST `/api/v1/brands/{brand_id}/creatives`
MVP manual import.

수동 등록은 자동 수집 누락을 보완하는 fallback이다.

```json
{
  "ownership_type":"competitor",
  "competitor_id":"uuid",
  "source":"manual",
  "source_url":"https://...",
  "media_type":"image",
  "title":null,
  "body_text":"광고 본문",
  "raw_payload":{}
}
```

### GET `/api/v1/brands/{brand_id}/creatives`
Filters 후보:
- competitor_id
- ownership_type
- media_type
- analyzed
- created_from/created_to

### GET `/api/v1/creatives/{creative_id}`
최신 analysis summary를 포함할 수 있다.

## 6.1 Market Content Collection

### POST `/api/v1/brands/{brand_id}/collection-sources`

```json
{
  "platform":"meta_ad_library",
  "scope":"competitor",
  "competitor_id":"uuid",
  "external_identifier":"https://www.facebook.com/competitor",
  "country_code":"VN",
  "language_code":"vi",
  "keywords":[],
  "sync_interval_hours":24
}
```

`industry` scope는 `competitor_id` 대신 하나 이상의 `keywords`를 요구한다.
자동 수집 source는 `meta_ad_library`, `tiktok_creative_center`를 허용한다. Meta는 Apify의 공개 광고 라이브러리 Actor, TikTok은 Creative Center Top Ads Actor로 수집하며 둘 다 Worker에서 실행한다. Meta의 `external_identifier`에는 Facebook 페이지 또는 광고 라이브러리 URL을 선택적으로 전달할 수 있다.

### GET `/api/v1/brands/{brand_id}/collection-sources`

브랜드에 설정된 수집 대상과 최근 동기화 상태를 반환한다.

### PATCH `/api/v1/collection-sources/{source_id}`

자동 수집 주기 또는 실행 상태를 변경한다.

```json
{"status":"paused","sync_interval_hours":24}
```

`status=active`로 재개하면 다음 scheduler tick에서 실행될 수 있도록 `next_sync_at`을 갱신한다.

### POST `/api/v1/collection-sources/{source_id}/sync`

```json
{"analyze_new_creatives":true}
```

Behavior:
1. tenant access와 source 상태 확인
2. `market_content_sync` Job 생성
3. Collector Worker enqueue
4. 외부 ID 기준 Creative upsert
5. 신규 Creative의 분석 Job enqueue

Celery Beat scheduler가 active source의 `next_sync_at`을 확인해 같은 sync API와 동일한 Job 흐름을 자동 실행한다.

Response `202`:

```json
{"job_id":"uuid","status":"queued"}
```

## 7. Creative Analysis

### POST `/api/v1/creatives/{creative_id}/analyses`

Behavior:
1. tenant access 확인
2. 동일 idempotency key의 active/completed job 확인
3. Job 생성
4. Celery enqueue
5. 빠르게 반환

Request:

```json
{"force":false}
```

Response `202`

```json
{"job_id":"uuid","status":"queued"}
```

### GET `/api/v1/creatives/{creative_id}/analyses`
분석 history 반환.

## 8. Jobs

### GET `/api/v1/jobs/{job_id}`

```json
{
  "id":"uuid",
  "job_type":"creative_analysis",
  "status":"processing",
  "progress":50,
  "error":null,
  "created_at":"...",
  "completed_at":null
}
```

다른 Organization의 job은 object existence leak을 줄이는 일관된 정책을 사용한다.

## 9. Usage

### GET `/api/v1/organizations/{organization_id}/usage`

Query:
- from
- to
- provider
- task

```json
{
  "period":{"from":"2026-08-01","to":"2026-08-31"},
  "estimated_cost_usd":12.43,
  "calls":312,
  "by_task":[
    {"task":"creative_analysis","calls":300,"estimated_cost_usd":8.12}
  ]
}
```

## 9.1 Billing

### GET `/api/v1/organizations/{organization_id}/billing`

Organization의 `$40` 플랜 상태, 현재 결제 기간의 제공량 사용, provider credit 잔액과 secret 없는 연결 상태를 반환한다. 다른 tenant는 404를 반환한다.

### POST `/api/v1/organizations/{organization_id}/billing/checkout`

Owner/Admin만 호출한다. local fake provider는 즉시 활성화하고, Stripe provider는 hosted Checkout URL을 반환한다.

### POST `/api/v1/organizations/{organization_id}/billing/portal`

활성 Stripe customer의 hosted Billing Portal URL을 반환한다.

### POST `/api/v1/billing/webhooks/stripe`

사용자 인증 대신 Stripe signature와 timestamp를 검증한다. subscription event는 Organization metadata로 tenant를 식별하며 같은 결제 기간 credit grant는 idempotent하다.

## 10. Error Model

```json
{
  "error":{
    "code":"CREATIVE_NOT_FOUND",
    "message":"Creative를 찾을 수 없습니다.",
    "request_id":"..."
  }
}
```

## 11. API 규칙

- UUID는 서버에서 생성.
- timestamps는 UTC 저장, ISO-8601 반환.
- 금액 계산은 float 대신 decimal/numeric.
- 외부 provider error message 전체를 사용자에게 노출하지 않는다.
- 중요한 POST에는 idempotency 전략을 고려한다.
- 대용량 파일 업로드는 추후 presigned upload 방식 사용.
