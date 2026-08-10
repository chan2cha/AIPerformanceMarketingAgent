# Testing Strategy

## 1. 목표

MVP에서 가장 위험한 실패는 예쁜 UI 부족이 아니라 다음이다.

1. 다른 고객사의 데이터가 보임
2. AI Job이 중복/유실됨
3. 외부 AI 실패가 앱 전체 오류가 됨
4. AI 호출은 됐지만 원가 기록이 안 됨
5. DB migration과 실제 코드 schema가 어긋남

테스트는 이 위험을 우선한다.

## 2. Backend Tests

### Unit
- domain validation
- AI router selection
- cost calculator
- service layer
- job state transition

### Integration
- PostgreSQL repository
- FastAPI endpoints
- migrations
- Celery task의 service 호출

실제 외부 AI Provider는 기본 테스트에서 mock/fake한다.

## 3. Mandatory Tenant Tests

### Given
- Organization A의 User A
- Organization B의 User B
- A의 Brand/Creative
- B의 Brand/Creative

### Assert
- User A는 A 데이터 조회 가능
- User A는 B 데이터 조회 불가
- URL에 B의 resource UUID를 직접 넣어도 조회 불가
- Job/Usage도 동일
- mutation도 동일

이 테스트가 깨지면 release blocker다.

## 4. Job Tests

상태 전이:

```text
queued → processing → completed
queued → processing → retry → processing → completed
queued → processing → failed
```

검증:
- completed 후 result 존재
- failed 후 sanitized error 존재
- retry 시 analysis 중복 생성 정책 일관성
- idempotency key가 있으면 동일 요청 중복 방지

## 5. AI Tests

Fake provider를 만든다.

Fake가 반환:
- deterministic structured result
- deterministic usage
- configurable timeout/error

검증:
- schema validation
- usage row 생성
- cost calculation
- provider exception mapping
- invalid structured output 처리

실제 Provider smoke test는 별도 opt-in test로 둔다. CI가 매번 실제 비용을 발생시키지 않도록 한다.

## 6. Frontend Tests

MVP 최소:
- typecheck
- lint
- login/authenticated route smoke
- Organization 생성 화면
- Brand 생성 화면
- Creative list
- Analysis 요청 후 Job 상태 표시

E2E는 핵심 flow부터 추가한다.

## 7. Definition of Done

기능은 다음을 만족해야 완료다.

- acceptance criteria 충족
- unit/integration test 추가 또는 합리적 사유
- lint/typecheck 통과
- migration 포함
- API contract와 implementation 불일치 없음
- 새로운 env var는 `.env.example`에 반영
- README 실행법 최신
- secret commit 없음

## 8. MVP Golden Path

```text
회원 인증
↓
Organization 생성
↓
Brand 생성
↓
Competitor 생성
↓
Creative 등록
↓
Analysis 요청
↓
Job queued
↓
Worker 처리
↓
CreativeAnalysis 저장
↓
ApiUsage 저장
↓
UI에서 결과 확인
```

Phase 1/2 완료 시 이 흐름을 자동 또는 반자동으로 검증한다.
