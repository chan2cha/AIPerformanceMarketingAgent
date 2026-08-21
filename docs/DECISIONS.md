# Architecture Decision Log

이 파일은 중요한 기술 결정을 짧게 기록한다. 결정을 바꾸는 것은 가능하지만 이유를 남긴다.

## ADR-001 — Modular Monolith

**Status:** Accepted

### Decision
Backend는 Modular Monolith + Worker로 시작한다.

### Reason
- 요구사항이 빠르게 변함
- 초기 팀/트래픽 규모에 마이크로서비스 비용이 불필요
- AI/데이터 Job만 별도 Worker가 필요

### Revisit when
- 독립적 scale bottleneck이 실제 측정됨
- 배포 주기가 모듈별로 크게 달라짐

---

## ADR-002 — TypeScript Web + Python Backend

**Status:** Accepted

### Decision
- Web: Next.js / TypeScript
- Backend: FastAPI / Python

### Reason
- SaaS UI 생태계
- AI/데이터 처리 Python 생태계
- 향후 분석/추천 로직 확장

---

## ADR-003 — PostgreSQL as Source of Truth

**Status:** Accepted

### Decision
핵심 business state는 PostgreSQL에 저장한다.

### Reason
Organization → Brand → Creative → Performance 관계가 명확하며 JSONB로 외부 raw payload 변화도 수용 가능하다.

---

## ADR-004 — Async Queue for AI Jobs

**Status:** Accepted

### Decision
장시간 AI 작업은 Celery + Redis를 통해 처리한다.

### Reason
- provider latency
- retries
- rate limit
- failure isolation
- 향후 worker scaling

---

## ADR-005 — Provider-independent AI Layer

**Status:** Accepted

### Decision
Provider SDK를 domain/service에서 직접 호출하지 않는다.

### Reason
- 가격 변동
- 품질 차이
- fallback
- vendor lock-in 완화

---

## ADR-006 — Usage Ledger from Day 1

**Status:** Accepted

### Decision
AI 호출마다 usage와 cost estimate를 저장한다.

### Reason
B2B AI SaaS의 unit economics를 검증해야 한다.

---

## ADR-007 — No Vector DB in MVP

**Status:** Accepted

### Decision
초기에는 별도 Vector DB를 사용하지 않는다.

### Revisit when
Creative 수가 증가하고 semantic similarity search가 제품 핵심 기능이 되면 PostgreSQL pgvector부터 검토한다.

---

## ADR-008 — No Automated Ad Launch in MVP

**Status:** Accepted

### Decision
광고 자동집행은 MVP에서 제외한다.

### Reason
초기 핵심 가설은 “다음 Creative Recommendation”의 가치 검증이며, 광고비 손실 위험/권한/운영 복잡도를 먼저 만들 필요가 없다.

---

## ADR-009 — Auth Adapter with Deterministic Local Mode

**Status:** Accepted

### Decision
- Backend 인증은 `AuthAdapter` 인터페이스 뒤에 둔다.
- local/test에서는 `Bearer dev:<subject>` 형식의 deterministic adapter를 사용한다.
- production에서는 dev auth를 금지하고 Supabase access token을 공개 JWKS로 검증한다.
- 초기 회원 초대 API는 제품 정책이 정해질 때까지 만들지 않고 Organization 생성자를 owner로 등록한다.

### Reason
- 실제 Supabase project/secret 없이 tenant integration test를 반복 가능하게 실행해야 한다.
- 도메인과 외부 Auth provider를 분리한다.
- dev 우회 인증이 production에서 활성화되는 사고를 방지한다.

---

## ADR-010 — OpenAI Responses API as the First Real AI Provider

**Status:** Accepted

### Decision

- 첫 실제 AI provider는 OpenAI로 선택한다.
- Creative text/metadata 분석은 Responses API의 Pydantic structured output을 사용한다.
- 기본 모델은 비용 민감·고빈도 workload용 `gpt-5.6-luna`로 고정한다.
- SDK 내부 retry는 비활성화하고 Celery Job retry 정책만 사용한다.
- 실제 API smoke test는 `RUN_OPENAI_SMOKE=1` 명시 시에만 실행한다.
- Phase 3에서는 image binary/URL을 provider에 전달하지 않고 Creative text/metadata만 분석한다.

### Reason

- 기존 `AIProvider`/`AIRouter` 경계를 유지하면서 structured output과 usage parsing을 제공한다.
- 기본 test/CI 및 local stack이 외부 네트워크나 비용 없이 계속 동작해야 한다.
- timeout, connection failure, rate limit, 5xx를 동일한 Job retry 정책으로 제어한다.
- API key를 Worker에만 주입해 frontend/API process의 불필요한 secret 접근을 줄인다.

### Revisit when

- 실제 Pilot 분석 품질이 Luna보다 상위 모델을 요구할 때
- image input의 제품 가치와 storage/privacy 정책이 확정될 때
- 두 번째 provider 또는 fallback routing이 필요할 때

---

## ADR-011 — Provider-independent Market Content Collectors

**Status:** Accepted

### Decision

- 광고 라이브러리 수집은 `AdLibraryCollector`와 router 뒤에서 실행한다.
- 플랫폼별 응답은 공통 `CollectedCreative` 형식으로 정규화한 후 도메인에 전달한다.
- 수집은 `market_content_sync` Job과 Celery Worker에서 비동기로 처리한다.
- 신규 수집 소재는 외부 ID로 중복을 제거하고 Creative 분석 Job에 연결한다.
- 로컬·테스트는 deterministic Fake Collector를 사용한다.
- 비공식 화면 스크래핑을 핵심 제품 경로로 채택하지 않는다.

### Reason

- Meta/TikTok 공식 데이터 접근 범위는 국가와 승인 유형에 따라 달라진다.
- 특정 플랫폼이나 데이터 판매자에 도메인이 종속되면 정책 변경 시 전체 수집 흐름이 깨진다.
- 동일 수집 파이프라인으로 API, 계약형 데이터 공급자, 향후 공식 adapter를 교체할 수 있어야 한다.

### Revisit when

- 베트남 상업 광고에 대한 공식·계약형 provider 접근이 확정될 때
- 공용 Market Creative DB의 법적·제품 정책이 확정될 때
