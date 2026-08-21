# PRD — AI Performance Marketing SaaS

## 1. Product Vision

커머스 기업이 매주 반복하는 아래 업무를 하나의 제품 흐름으로 연결한다.

```text
시장/경쟁사 광고 관찰
        ↓
Creative 패턴 분석
        ↓
자사 광고 성과 비교
        ↓
다음 광고 가설 추천
        ↓
Creative 기획/생성
        ↓
집행
        ↓
성과 학습
        ↺
```

초기 제품은 **Observe → Learn → Recommend**에 집중한다.

## 2. 문제 정의

중소·성장기 커머스 기업의 마케팅팀은 경쟁사 광고 탐색, 광고 레퍼런스 정리, Hook/Offer/CTA 분석, 새로운 소재 기획, 성과 분석, 다음 테스트 결정을 반복한다.

현재 이 과정은 Meta/TikTok/Notion/Excel/AI 도구/디자인 도구 사이를 사람이 이동하면서 진행된다.

**핵심 문제는 툴이 없는 것이 아니라 Workflow가 연결되어 있지 않다는 점이다.**

## 3. 초기 ICP

### Primary
월 광고비 약 1,000만~1억원 수준의 D2C/커머스 브랜드.

특징:
- 마케팅팀 1~5명
- Meta 중심의 퍼포먼스 광고 집행
- 매주 신규 Creative 필요
- 인하우스 운영 비중이 있음
- 광고 소재 기획/분석이 병목

### 초기 Vertical 후보
- 뷰티
- 패션
- 식품/건강식품
- 리빙
- 반려동물

초기 Pilot에서는 하나의 Vertical을 선택한다.

## 4. User Roles

### Owner
- Organization 생성
- 팀 관리
- 브랜드 관리
- 사용량/요금 확인

### Marketer
- 브랜드/경쟁사 관리
- Creative 확인
- 분석 실행
- 향후 Recommendation 사용

MVP에서는 Owner/Admin/Member 수준의 단순 권한으로 충분하다.

## 5. MVP 핵심 User Story

### Authentication
- 사용자는 로그인할 수 있다.
- 로그인한 사용자는 자신이 속한 Organization만 접근할 수 있다.

### Organization
- 사용자는 Organization을 생성할 수 있다.
- Organization은 여러 사용자를 가질 수 있다.

### Brand
- Organization은 하나 이상의 Brand를 등록할 수 있다.
- Brand는 website, industry, description, target customer 등의 정보를 가진다.

### Competitor
- Brand는 여러 Competitor를 등록할 수 있다.
- 경쟁사에는 이름, URL, 플랫폼 식별자/URL 등을 저장할 수 있다.

### Creative
- 사용자는 브랜드, 업종, 타깃 국가·언어, 경쟁사를 한 번 설정할 수 있다.
- 시스템은 설정을 기반으로 광고 라이브러리와 허용된 데이터 소스에서 신규 Creative를 주기적으로 탐색한다.
- 수집된 Creative는 출처와 외부 ID를 기록하고 중복 없이 저장한다.
- 자동 수집이 지원되지 않는 콘텐츠는 URL 또는 원문으로 보완 등록할 수 있다.
- Creative는 source, source URL, media type, asset, raw payload를 저장할 수 있다.
- Creative 목록을 조회하고 필터링할 수 있다.

### AI Analysis
- 사용자는 Creative 분석을 요청할 수 있다.
- 요청은 비동기 Job으로 처리된다.
- 결과는 Hook, Pain Point, Format, Offer, CTA 등의 구조화 값으로 저장된다.
- 분석 실패 시 실패 상태와 에러를 확인할 수 있다.

### Usage
- 모든 AI 호출에 대한 사용량과 원가 추정치가 기록된다.
- Organization별 사용량 집계가 가능하다.

## 6. Creative Analysis Output

최소 구조:

```json
{
  "hook_type": "problem",
  "hook_text": "string",
  "pain_points": ["string"],
  "message_type": "testimonial",
  "format": "ugc",
  "offer_type": "discount",
  "offer_text": "20% 할인",
  "cta_type": "shop_now",
  "cta_text": "지금 구매하기",
  "product_focus": "string",
  "summary": "string",
  "confidence": 0.86
}
```

필드는 실제 데이터 검증 과정에서 확장 가능하나 무분별하게 늘리지 않는다.

## 7. Phase 2 이후 핵심 User Story

### Market Intelligence
- 경쟁사별 Meta/TikTok 수집 소스를 설정한다.
- 국가·언어·업종 키워드로 시장 광고 탐색 범위를 설정한다.
- 수집은 비동기 Job으로 실행되며 최근 성공·실패 상태를 확인한다.
- 신규 광고는 자동 분석되어 경쟁사·업종 패턴의 입력으로 사용된다.
- 플랫폼이 제공하지 않는 국가·광고 유형은 지원 범위를 사용자에게 명확히 표시한다.

### Performance
- Meta Ad Account 연결
- Campaign/Ad/Creative 성과 일 단위 sync
- Creative와 성과 연결
- CTR/CPA/ROAS 기반 분석

### Recommendation
- 시장 Creative 패턴과 자사 성과를 입력으로 사용
- 이번 주 테스트할 광고 가설 생성
- 추천 근거 설명
- 추천이 실제 집행됐는지 기록

## 8. Non-functional Requirements

### Security
- tenant isolation
- secret management
- audit 가능한 AI usage

### Reliability
- 외부 AI API 실패가 전체 앱 장애로 이어지지 않아야 함
- worker retry
- job status 저장

### Observability
- request error
- worker error
- AI provider error
- job duration
- 고객별 AI cost 추적

### Performance
MVP 단계에서는 대규모 트래픽보다 신뢰성과 개발 속도를 우선한다.

## 9. 성공 기준

### MVP 기술 성공
- Organization 생성부터 수집 소스 설정, Creative 자동 수집·분석 완료까지 end-to-end 동작
- tenant isolation 테스트 성공
- AI 호출 원가 추적 가능

### Product 성공
Pilot 고객이:
- 실제 경쟁사를 설정하고 수집된 Creative를 반복적으로 사용
- 주기적으로 분석 결과를 확인
- 다음 광고 기획에 분석 결과를 사용

## 10. MVP에서 의도적으로 제외

- 자동 광고 집행
- 완전 자율 마케팅 Agent
- 이미지/영상 대량 생성
- 자체 학습 모델
- 경쟁사 실제 ROAS 추정
- 복잡한 attribution
- 광고대행사 다계정 전용 기능
