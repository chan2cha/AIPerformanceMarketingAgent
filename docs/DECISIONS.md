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
