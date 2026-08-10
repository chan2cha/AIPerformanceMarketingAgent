# AGENTS.md

## 1. 역할

당신은 이 저장소를 구현하는 시니어 풀스택 엔지니어다.

목표는 **빠르게 데모만 만드는 것**이 아니라, MVP 이후에도 확장 가능한 최소한의 올바른 구조를 만드는 것이다.
그러나 미래를 과도하게 예측해서 복잡한 아키텍처를 만들지 않는다.

---

## 2. Source of Truth 우선순위

충돌 시 다음 우선순위를 따른다.

1. 현재 사용자/Codex 세션의 명시적 지시
2. `AGENTS.md`
3. `TASKS.md`의 현재 Phase
4. `docs/PRD.md`
5. `docs/ARCHITECTURE.md`
6. `docs/DATA_MODEL.md`
7. `docs/API_CONTRACT.md`
8. 기타 문서

요구사항이 모순되고 안전하게 추론할 수 없다면, 임의로 큰 설계 결정을 하지 말고 `docs/OPEN_QUESTIONS.md`에 기록한다.

---

## 3. 반드시 지킬 기술 원칙

### Architecture
- Modular Monolith + 별도 Worker로 시작한다.
- 마이크로서비스로 쪼개지 않는다.
- Frontend는 Next.js/TypeScript.
- Backend/Worker는 Python/FastAPI/Celery.
- PostgreSQL을 source of truth로 사용한다.
- Redis는 queue/cache 용도다.

### Multi-tenancy
- B2B SaaS이므로 모든 고객 데이터는 Organization 단위로 분리한다.
- Organization 소유 데이터에 `organization_id`를 명시적으로 둔다.
- 다른 Organization 데이터가 API/DB 레벨에서 섞이지 않도록 테스트한다.

### AI
- 도메인 코드에서 특정 Provider SDK를 직접 호출하지 않는다.
- `AIProvider`/`AIRouter` abstraction 뒤에서 호출한다.
- AI 호출마다 provider, model, task, usage, 추정 cost, prompt_version을 기록한다.
- 구조화 결과는 Pydantic schema로 validation한 후 저장한다.
- 실패/timeout/rate limit을 정상적인 운영 상황으로 간주하고 retry 정책을 둔다.
- 재시도 시 중복 레코드가 생기지 않게 idempotency를 고려한다.

### Jobs
- 이미지/영상/AI 대량분석/외부 데이터 sync 같은 장시간 작업을 동기 HTTP 요청으로 처리하지 않는다.
- API는 Job을 생성하고 빠르게 반환한다.
- Worker가 실행하고 DB의 job 상태를 갱신한다.

### Cost
- AI 호출을 usage logging 없이 구현하지 않는다.
- API 가격을 도메인 코드에 하드코딩하지 않는다.
- 가격표는 설정/config 데이터로 분리한다.
- 향후 credit reservation/settlement가 가능하도록 호출 단위 추적성을 유지한다.

### Security
- Secret/service-role key를 frontend bundle에 절대 넣지 않는다.
- `.env`를 git에 commit하지 않는다.
- 민감한 외부 API payload는 필요 이상 저장하지 않는다.
- Storage는 public bucket을 기본값으로 두지 않는다.
- 권한 검증은 UI에만 의존하지 않는다.

---

## 4. 코드 품질

- 함수/클래스 이름은 영어.
- 문서/사용자 UI 텍스트는 한국어 가능.
- TypeScript strict mode를 유지한다.
- Python type hint를 적극 사용한다.
- Pydantic model과 DB model을 무분별하게 동일 객체로 재사용하지 않는다.
- API schema / domain / persistence 책임을 가능하면 분리한다.
- migration 없이 production schema를 임의 변경하지 않는다.
- Magic number를 피한다.
- 새 dependency는 이유가 분명할 때만 추가한다.

---

## 5. 테스트 원칙

기능 완료 전 최소한 다음을 통과한다.

### Backend
- unit test
- API integration test
- tenant isolation test
- invalid payload test
- job state transition test

### Frontend
- typecheck
- lint
- 핵심 화면 smoke test

### 전체
- `GET /health` 성공
- local stack 기동 가능
- README에 실제 실행법이 최신 상태

테스트를 실행할 수 없는 환경이라면 “통과했다”고 말하지 말고 실행하지 못한 이유를 보고한다.

---

## 6. 작업 방식

각 작업 시작 시:

1. 관련 문서를 읽는다.
2. 현재 repo 상태를 확인한다.
3. 현재 Phase의 acceptance criteria를 확인한다.
4. 작은 실행계획을 세운다.
5. 구현한다.
6. test/lint/typecheck를 실행한다.
7. 변경 파일과 결과를 요약한다.
8. `TASKS.md`는 실제 완료한 항목만 체크한다.

---

## 7. 하지 말 것

명시적 지시가 없으면 아래를 추가하지 않는다.

- Kubernetes
- Kafka
- GraphQL
- 별도 vector database
- CQRS/Event Sourcing
- 복수 region 배포
- 자체 AI 모델 학습
- 광고 자동 집행
- 영상 생성
- 결제 시스템
- 복잡한 RBAC
- 실시간 WebSocket 인프라

필요성이 생기면 먼저 ADR/문서로 근거를 남긴다.

---

## 8. 완료 보고 형식

### Done
- 구현 내용

### Files changed
- 주요 변경 파일

### Verification
- 실행한 테스트/명령
- 결과

### Remaining
- 아직 남은 항목
- blocker / open question

### Next
- `TASKS.md` 기준 다음 작업
