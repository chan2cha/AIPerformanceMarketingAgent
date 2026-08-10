# AI, Usage Cost & Credits

## 1. 목표

이 제품은 고객이 직접 AI 기능을 사용하므로 **사용량이 매출보다 빠르게 증가할 수 있는 구조**를 처음부터 막아야 한다.

> AI 호출은 기능이 아니라 원가가 발생하는 transaction이다.

## 2. Provider-independent Design

```text
CreativeAnalysisService
        ↓
      AIRouter
        ↓
     AIProvider
```

MVP는 1개 provider부터 시작해도 된다. 단 interface, usage logging, model config, prompt versioning은 처음부터 provider-independent하게 만든다.

## 3. Task Types

초기 enum 후보:

```text
creative_classification
creative_analysis
brand_profile
weekly_strategy
recommendation
copy_generation
image_generation
video_generation
```

MVP Phase 1~2에는 `creative_analysis`만 실제 구현해도 된다.

## 4. Model Routing

향후:
- Cheap model: 분류/필드 추출/대량 tagging
- Mid model: Creative 비교/패턴 요약
- High capability model: 주간 전략/복합 recommendation

model name을 코드 곳곳에 문자열로 쓰지 않는다.

## 5. Usage Ledger

모든 provider call 완료 후 기록:
- organization_id
- user_id
- job_id
- provider/model/task
- input/output units
- unit type
- latency
- estimated cost
- provider request id

Provider가 usage를 반환하지 못하면 가능한 범위에서 추정하고 `estimated`임을 유지한다.

## 6. Pricing Config

가격은 business logic에 하드코딩하지 않는다.

개념:

```yaml
providers:
  provider_a:
    model_x:
      input_per_million: ...
      output_per_million: ...
      effective_from: ...
```

실제 단가는 운영 시점 가격표를 기준으로 업데이트한다. 과거 usage의 계산값은 호출 당시 값으로 보존한다.

## 7. Credit Model — Later Phase

추천 구조:

```text
Base Subscription
+
Included Credits
+
Overage / Credit Pack
```

고객에게 노출하는 Credit과 실제 provider 원가는 동일 단위일 필요가 없다. Credit은 가격 변동, margin, 모델 차이를 흡수하는 abstraction이다.

## 8. Reservation / Settlement

영상처럼 비용이 큰 작업:

```text
requested
  ↓
credit reservation
  ↓
provider call
  ↓
success → settle
failure → release/refund
```

MVP Creative Analysis에는 전체 credit engine을 만들지 않는다. 그러나 `api_usage`와 `job_id` 관계는 이후 정산이 가능하도록 유지한다.

## 9. Cost Guardrails

향후 Organization별:
- monthly_cost_soft_limit
- monthly_cost_hard_limit
- model allowlist
- generation quota

## 10. Cost KPI

반드시 볼 것:

`AI + Infra Variable Cost / Revenue`

추가:
- cost per organization
- cost per active brand
- cost per analyzed creative
- cost per recommendation
- provider/model별 cost
- retry waste cost

## 11. 중복 분석 방지

장기 구조:

```text
Creative fingerprint
      ↓
Existing structured analysis?
      ├─ yes → reuse
      └─ no  → AI call
```

초기에는 tenant data로 단순 구현하고 shared market DB 도입 시 deduplication을 확장한다.

## 12. Prompt Versioning

예:

```text
backend/app/ai/prompts/
└── creative_analysis/
    ├── v1.md
    └── schema_v1.py
```

분석 row에 `prompt_version`, `schema_version`, `provider`, `model`을 저장한다. Prompt 수정 시 기존 분석을 조용히 덮어쓰지 않는다.
