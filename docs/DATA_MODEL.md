# Data Model

## 1. 원칙

1. B2B Multi-tenant.
2. 고객 데이터는 `organization_id`로 명확히 scope한다.
3. 외부 Auth 사용자 ID와 내부 domain 데이터를 분리 가능하게 설계한다.
4. AI 결과는 재현/추적 가능하도록 model/prompt version을 남긴다.
5. AI 원가는 반드시 호출 단위로 기록한다.
6. Performance는 향후 일 단위 fact table로 저장한다.

## 2. Core Relationships

```text
User
  │
  └──< Membership >── Organization
                         │
                         └──< Brand
                               │
                               ├──< Competitor
                               ├──< CollectionSource
                               │
                               └──< Creative
                                      │
                                      ├──< CreativeAsset
                                      ├──< CreativeAnalysis
                                      └──< AdPerformanceDaily (later)

Organization
  ├──< Job
  ├──< ApiUsage
  ├─── Subscription
  └──< CreditLedger
```

## 3. Core Tables

### users

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| auth_user_id | text/uuid | external auth identifier |
| email | text | normalized |
| name | text nullable | |
| created_at | timestamptz | |

Unique: `auth_user_id`

### organizations

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| name | text | |
| plan | text | initial default |
| status | text | active/suspended |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### memberships

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK |
| user_id | uuid | FK |
| role | text | owner/admin/member |
| created_at | timestamptz | |

Unique: `(organization_id, user_id)`

### brands

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK |
| name | text | |
| website | text nullable | |
| industry | text nullable | |
| description | text nullable | |
| target_customer | text nullable | |
| brand_tone | text nullable | |
| raw_profile | jsonb nullable | evolving AI enrichment |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Index: `organization_id`

### competitors

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK |
| brand_id | uuid | FK |
| name | text | |
| website | text nullable | |
| instagram_url | text nullable | |
| meta_page_id | text nullable | |
| tiktok_url | text nullable | |
| metadata | jsonb nullable | |
| created_at | timestamptz | |

`organization_id`를 중복 저장해 tenant query를 명확하게 한다.

### collection_sources

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK, tenant scope |
| brand_id | uuid | FK |
| competitor_id | uuid nullable | 경쟁사 관찰이면 필수 |
| created_by_user_id | uuid nullable | scheduler audit/requester |
| platform | text | meta_ad_library/tiktok_creative_center |
| scope | text | competitor/industry |
| external_identifier | text nullable | page/account/provider identifier |
| country_code | text | ISO 3166-1 alpha-2 |
| language_code | text nullable | 분석 대상 언어 |
| keywords | jsonb | 업종·현지 검색어 |
| status | text | active/paused |
| sync_interval_hours | integer | 1..168 |
| next_sync_at | timestamptz nullable | scheduler 기준 시각 |
| last_attempt_at | timestamptz nullable | 최근 실행 시도 |
| last_sync_at | timestamptz nullable | |
| last_error_code | text nullable | sanitized source state |
| created_at/updated_at | timestamptz | |

플랫폼 credential이나 secret은 이 테이블에 직접 저장하지 않는다. 외부 콘텐츠는 `creatives`의 `(organization_id, source, source_external_id)`로 중복을 방지한다.

### creatives

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid nullable | shared market data 확장 고려 |
| brand_id | uuid nullable | |
| competitor_id | uuid nullable | |
| ownership_type | text | own/competitor/market |
| source | text | manual/meta/tiktok/etc |
| source_external_id | text nullable | |
| source_url | text nullable | |
| media_type | text | image/video/carousel/text |
| title | text nullable | |
| body_text | text nullable | |
| first_seen_at | timestamptz nullable | |
| last_seen_at | timestamptz nullable | |
| raw_payload | jsonb nullable | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

MVP에서는 tenant-owned data로 먼저 구현해도 된다. Shared market DB를 실제 도입하기 전까지 `organization_id is null` 접근 정책을 임의로 열지 않는다.

### creative_assets

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| creative_id | uuid | FK |
| object_key | text | storage key |
| content_type | text | |
| size_bytes | bigint nullable | |
| checksum | text nullable | |
| width | integer nullable | |
| height | integer nullable | |
| duration_seconds | numeric nullable | |
| created_at | timestamptz | |

### creative_analyses

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK |
| creative_id | uuid | FK |
| status | text | completed/superseded |
| hook_type | text nullable | |
| hook_text | text nullable | |
| pain_points | jsonb | array |
| message_type | text nullable | |
| format | text nullable | |
| offer_type | text nullable | |
| offer_text | text nullable | |
| cta_type | text nullable | |
| cta_text | text nullable | |
| product_focus | text nullable | |
| summary | text nullable | |
| confidence | numeric nullable | 0..1 |
| provider | text | |
| model | text | |
| prompt_version | text | |
| schema_version | text | |
| raw_result | jsonb nullable | |
| created_at | timestamptz | |

분석 history를 유지하고 최신 결과는 query/view로 조회한다.

### jobs

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK |
| user_id | uuid nullable | requester |
| job_type | text | |
| status | text | queued/processing/completed/failed/cancelled |
| progress | integer nullable | 0..100 |
| target_type | text nullable | creative/etc |
| target_id | uuid nullable | |
| idempotency_key | text nullable | |
| attempts | integer | default 0 |
| error_code | text nullable | sanitized |
| error_message | text nullable | sanitized |
| started_at | timestamptz nullable | |
| completed_at | timestamptz nullable | |
| created_at | timestamptz | |

### api_usage

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK |
| user_id | uuid nullable | |
| job_id | uuid nullable | |
| provider | text | |
| model | text | |
| task | text | |
| input_units | bigint nullable | token/etc |
| output_units | bigint nullable | |
| unit_type | text | tokens/images/seconds/etc |
| estimated_cost_usd | numeric | |
| provider_request_id | text nullable | |
| latency_ms | integer nullable | |
| created_at | timestamptz | |

Indexes:
- `(organization_id, created_at)`
- `(provider, model, created_at)`

### subscriptions

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | FK, unique tenant subscription |
| plan_code | text | `pilot_40` |
| status | text | inactive/trialing/active/past_due/cancelled |
| billing_provider | text | fake/stripe |
| external_customer_id | text nullable | provider reference |
| external_subscription_id | text nullable | provider reference |
| current_period_start | timestamptz nullable | |
| current_period_end | timestamptz nullable | |

### credit_ledger

| column | type | notes |
|---|---|---|
| id | uuid | PK |
| organization_id | uuid | tenant scope |
| subscription_id | uuid nullable | FK |
| job_id | uuid nullable | FK |
| entry_type | text | grant/reservation/settlement/release/adjustment |
| amount_usd | numeric | signed append-only amount |
| idempotency_key | text | unique per Organization |
| description | text | sanitized operation description |
| metadata | jsonb | non-secret period/cost metadata |
| created_at | timestamptz | |

잔액은 ledger 합계로 계산한다. 새 결제 기간에는 이전 미사용 credit을 adjustment로 만료한 뒤 월 credit을 grant한다.

## 4. Later Tables

### ad_accounts
- organization_id
- brand_id
- platform
- external_account_id
- encrypted credential reference
- status

### ad_performance_daily
- organization_id
- brand_id
- creative_id
- date
- spend
- impressions
- clicks
- conversions
- revenue
- ctr/cpc/cpa/roas
- raw_payload

### recommendations
- organization_id
- brand_id
- period_start
- hypothesis
- rationale
- recommended_format/hook/offer
- priority/status
- provider/model/prompt_version

### experiments
추천 → 실제 집행 → 성과 피드백 루프 연결.

## 5. Tenant Isolation Rule

Organization-owned endpoint의 모든 query는 다음 조건을 만족해야 한다.

```text
authenticated user
  ↓
membership 확인
  ↓
authorized organization
  ↓
organization-scoped query
```

ID를 알고 있다는 이유만으로 다른 tenant의 Brand/Creative/Job에 접근할 수 없어야 한다. 이 규칙은 자동 테스트로 보장한다.
