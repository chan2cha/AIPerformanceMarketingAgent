# AI 퍼포먼스 마케팅 운영 SaaS 사업기획서

> **가칭:** AI Performance Marketing Agent  
> **사업 형태:** B2B SaaS + Usage Credit  
> **핵심 고객:** 중소·성장기 커머스/D2C 브랜드의 인하우스 마케팅팀  
> **핵심 가치:** 경쟁사 리서치 → 광고 기획 → 소재 제작 → 성과 분석 → 다음 실험 제안의 반복 업무를 AI로 연결·자동화

---

## 0. Executive Summary

커머스 브랜드의 마케팅 업무는 본질적으로 반복적인 실험의 연속이다.

1. 경쟁 브랜드의 광고와 콘텐츠를 찾는다.
2. 잘 작동할 가능성이 높은 패턴을 분석한다.
3. 자사 브랜드에 맞게 변형한다.
4. 광고 소재를 제작한다.
5. Meta/TikTok 등에 집행한다.
6. CTR, CPA, ROAS 등 성과를 분석한다.
7. 결과를 바탕으로 다음 광고 가설을 만든다.
8. 다시 제작·집행한다.

현재 이 과정은 마케터, 디자이너, 대행사가 여러 도구를 오가며 수작업으로 수행한다.

본 서비스는 단순한 **AI 광고 생성기**가 아니라 이 전체 루프를 하나로 연결하는 **AI Performance Marketing Agent**를 목표로 한다.

### 한 문장 정의

> **중소 커머스 기업의 마케팅팀이 경쟁사와 자사 광고 데이터를 기반으로 다음에 테스트할 광고를 지속적으로 찾아내고 제작할 수 있도록 돕는 AI 마케팅 운영 SaaS**

### 핵심 제품 철학

**Benchmark → Analyze → Adapt → Test → Learn → Repeat**

경쟁사 광고를 그대로 복제하는 것이 아니라, 성공 가능성이 있는 패턴을 구조화하고 자사 브랜드·고객 데이터와 결합해 다음 실험을 제안한다.

---

# 1. 문제 정의

## 1.1 고객이 겪는 핵심 문제

소규모·성장기 커머스 기업은 마케팅이 매우 중요하지만 충분한 인력을 확보하기 어렵다.

대표적인 반복 업무는 다음과 같다.

- 경쟁사 광고 모니터링
- 최근 광고 트렌드 파악
- 광고 Hook/Offer/CTA 분석
- 소재 아이디어 회의
- 광고 카피 작성
- 이미지·영상 기획
- 소재 제작
- 광고 계정 성과 확인
- CTR/CPA/ROAS 분석
- 다음 테스트 방향 결정
- 보고서 작성

이 과정은 매주 반복된다.

### 현재 상태

```text
마케터
  ↓
Meta Ad Library / TikTok / Instagram 탐색
  ↓
Notion / Excel / PPT 정리
  ↓
아이디어 회의
  ↓
ChatGPT / Canva / 영상툴
  ↓
Meta Ads 집행
  ↓
Meta / GA 분석
  ↓
회의
  ↓
다시 처음부터
```

### 문제의 본질

**개별 기능의 부재가 아니라 기능 간 연결이 끊겨 있다는 것.**

AI 카피 도구, 이미지 생성기, 영상 생성기, 광고 분석 도구는 이미 존재하지만 사용자가 여전히 직접 정보를 옮기고 판단해야 한다.

---

## 1.2 고객이 실제로 사고 싶은 것

고객은 다음을 원하지 않는다.

> “AI 이미지 생성 툴 하나 더.”

고객이 원하는 것은 다음과 가깝다.

> **“이번 주 어떤 광고를 만들어야 하는지 알려주고, 빠르게 만들어주며, 광고 결과를 보고 다음 주 무엇을 테스트할지 다시 알려주는 시스템.”**

따라서 제품의 경쟁 단위는 **Creative Generation**이 아니라 **Marketing Workflow Automation**이어야 한다.

---

# 2. 타깃 고객 세분화

## 2.1 고객 세그먼트

| 고객군 | 월 광고비 예시 | 조직 특성 | Pain Point | 초기 타깃 적합도 |
|---|---:|---|---|---|
| 1인 쇼핑몰 | 100~500만원 | 대표 직접 운영 | 마케팅 지식 부족 | 중 |
| 초기 D2C 브랜드 | 500~3,000만원 | 마케터 1~2명 | 소재 생산 부족 | 매우 높음 |
| 성장기 D2C 브랜드 | 3,000만~1억원+ | 마케팅팀 2~5명 | 테스트/분석 복잡 | 매우 높음 |
| 중견 소비재 기업 | 1억원+ | 인하우스 조직 | 협업/보고 체계 복잡 | 중 |
| 대형 브랜드 | 대규모 | 전문팀/대행사 보유 | 보안/시스템 통합 | 초기 낮음 |
| 광고대행사 | 다수 계정 | 반복 업무 다량 | 다계정 운영 비효율 | 2차 타깃 매우 높음 |

---

## 2.2 초기 ICP

### 추천 ICP

**월 광고비 약 1,000만~1억원을 집행하는 D2C/커머스 브랜드**

조건 예시:

- 온라인 매출 비중이 높음
- Meta/TikTok 광고를 지속적으로 집행
- 마케터 1~5명
- 신규 광고 소재를 매주 제작
- 콘텐츠 제작 속도가 성과의 병목
- 광고대행사 전체 위탁보다는 인하우스 운영 비중이 있음

### 우선 공략 카테고리

1. 화장품/뷰티
2. 패션
3. 건강식품/식품
4. 생활용품
5. 반려동물
6. 리빙
7. 기타 반복 구매형 D2C

초기에는 **한 카테고리에 집중**하는 것이 좋다.

이유:

- 경쟁사 풀이 겹침
- 광고 포맷이 유사함
- 분석 데이터 재사용 가능
- 영업 메시지가 선명해짐
- 추천 품질을 빠르게 높일 수 있음

---

# 3. 기존 대안 / 경쟁 분석

## 3.1 고객이 현재 사용하는 대안

| 업무 | 현재 대안 | 문제점 |
|---|---|---|
| 경쟁사 광고 탐색 | Meta Ad Library, TikTok Creative Center | 사람이 직접 찾아야 함 |
| 광고 저장/레퍼런스 | Notion, Excel, Swipe tools | 분석/성과와 연결 안 됨 |
| 크리에이티브 분석 | 전문 분석 SaaS | 생성·집행까지 단절 |
| 카피 생성 | ChatGPT, Claude, Gemini | 브랜드·성과 데이터 연결 부족 |
| 이미지 생성 | Canva, OpenAI Image, FLUX 등 | 성과 기반 추천 아님 |
| 영상 생성 | Runway, Veo, Luma 등 | 제작은 하지만 전략 판단 부족 |
| 광고 집행 | Meta Ads, TikTok Ads | 경쟁사/콘텐츠 기획과 단절 |
| 성과 분석 | Meta, GA, 대시보드 SaaS | 다음 광고 기획까지 자동 연결되지 않음 |

---

## 3.2 경쟁 구도

시장은 크게 다음처럼 나뉜다.

### A. 광고 인텔리전스
- 경쟁사 광고 탐색
- 광고 저장
- Creative 분석
- 패턴 파악

### B. AI Creative Generation
- 카피
- 이미지
- 영상
- UGC형 콘텐츠

### C. 광고 집행/최적화
- Meta
- TikTok
- Google

### D. 성과 분석
- ROAS
- CPA
- CTR
- Attribution
- Creative performance

### 시장의 빈틈

각 영역은 이미 강한 솔루션이 있지만, 대부분 **한 기능 또는 한 구간에 집중**되어 있다.

따라서 기회는:

> **경쟁사 인사이트 + 자사 성과 + 신규 Creative Recommendation + 제작을 하나의 반복 루프로 연결하는 것**

---

# 4. 차별화 포지셔닝

## 4.1 잘못된 포지셔닝

다음 메시지는 피해야 한다.

- “AI로 광고 이미지를 만들어드립니다.”
- “AI가 광고 카피를 써드립니다.”
- “경쟁사 광고를 분석해드립니다.”
- “광고 성과를 AI로 분석합니다.”

기능 단위로는 쉽게 복제될 수 있다.

---

## 4.2 추천 포지셔닝

### 카테고리

**AI Performance Marketing Agent**

또는

**AI Creative Intelligence & Experiment Platform**

### 핵심 메시지

> **“다음에 어떤 광고를 테스트해야 할지 계속 찾아주는 AI 마케팅팀.”**

---

## 4.3 제품 루프

```text
[시장/경쟁사 관찰]
        ↓
[광고 패턴 구조화]
        ↓
[자사 과거 성과 비교]
        ↓
[다음 광고 가설 생성]
        ↓
[Creative Brief / Script 생성]
        ↓
[이미지·영상 생성]
        ↓
[사용자 승인]
        ↓
[광고 집행]
        ↓
[성과 데이터 수집]
        ↓
[AI 분석]
        ↓
[다음 실험 제안]
        ↺
```

---

## 4.4 핵심 차별화 요소

### ① Market Intelligence

경쟁사의 신규 광고를 지속적으로 수집하고 다음 항목으로 구조화한다.

- Hook
- Pain Point
- Product
- Format
- UGC 여부
- Offer
- CTA
- 영상 길이
- 메시지 유형
- Landing Page
- 광고 지속 기간

경쟁사의 실제 ROAS는 알 수 없으므로, 광고 지속 기간 등은 **성과의 확정값이 아닌 signal**로 취급한다.

---

### ② My Performance Intelligence

고객사의 광고 계정을 연결한다.

수집 예시:

- Spend
- Impression
- CTR
- CPC
- CPA
- CVR
- ROAS
- Creative ID
- Campaign
- Ad set
- Audience

---

### ③ Next Creative Recommendation

가장 중요한 기능.

예:

> 최근 경쟁사 10곳에서 문제 공감형 UGC가 증가하고 있습니다.  
> 그러나 귀사에서는 할인형 소재보다 후기형 소재의 ROAS가 높습니다.  
> 이번 주에는 후기형 UGC 5개와 문제 공감형 Hook 3개를 테스트하는 것을 권장합니다.

즉 단순 분석이 아니라 **다음 행동까지 제안**한다.

---

### ④ Brand Adaptation

경쟁사 콘텐츠를 복제하지 않는다.

```text
Competitor Creative
        ↓
Pattern Extraction
        ↓
Brand Rule / Product USP
        ↓
Customer Performance Data
        ↓
New Creative Hypothesis
```

브랜드 고유성을 유지하면서 유효한 패턴만 활용한다.

---

# 5. 제품 구성

## 5.1 사용자 초기 설정

### STEP 1. 브랜드 등록
입력:
- 홈페이지 URL
- 주요 상품
- 가격
- 브랜드 설명
- 타깃 고객

AI 추출:
- USP
- 제품 카테고리
- 브랜드톤
- 주요 Pain Point
- 후기 키워드
- 이미지 자산

### STEP 2. 경쟁사 등록
사용자가 5~20개 경쟁 브랜드를 입력.

### STEP 3. 광고 계정 연결
- Meta
- TikTok
- 기타 채널

### STEP 4. 목표 입력
예:
- 신규 고객 CPA 절감
- ROAS 개선
- 신제품 테스트
- 신규 Creative 확보

---

## 5.2 주요 메뉴

```text
Dashboard
├── Competitors
├── Creative Library
├── Market Insights
├── My Ads
├── Performance
├── This Week Tests
├── Creative Studio
└── Reports
```

---

## 5.3 MVP 기능 우선순위

### MVP 1 — Observe
- 경쟁사 등록
- 광고 수집
- 광고 분류
- Hook/Offer/CTA 추출

### MVP 2 — Learn
- 자사 Meta 광고 데이터 연결
- Creative별 성과 분석
- 경쟁사 패턴과 비교

### MVP 3 — Recommend
- 다음 테스트 아이디어 생성
- Creative Brief
- 카피
- 숏폼 Script

### MVP 4 — Generate
- 이미지 생성
- 영상 생성
- Variations

### MVP 5 — Launch & Optimize
- 광고 계정으로 전송
- 성과 자동 수집
- 다음 실험 자동 생성

**초기에는 Launch 자동화까지 들어가지 않아도 된다.**

---

# 6. AI/API 아키텍처

## 6.1 핵심 원칙

자체 AI 모델을 처음부터 만들 필요는 없다.

서비스는 여러 AI API를 조합하는 **Orchestration Layer** 역할을 한다.

```text
             [Our SaaS]
                 │
      ┌──────────┼──────────┐
      ↓          ↓          ↓
     LLM       Image      Video
      │          │          │
 OpenAI       FLUX       Runway
 Claude       OpenAI     Veo
 Gemini       Google     Luma
      │          │          │
      └──────────┼──────────┘
                 ↓
        Performance Database
                 ↓
        Recommendation Engine
```

---

## 6.2 기능별 API 예시

| 영역 | 가능한 공급자 | 역할 |
|---|---|---|
| LLM | OpenAI / Anthropic / Google | 분석, 카피, 전략 |
| 이미지 | OpenAI / FLUX / Google | 광고 이미지 |
| 영상 | Runway / Veo / Luma 등 | 숏폼/제품 영상 |
| 음성 | ElevenLabs 등 | 광고 내레이션 |
| 광고 데이터 | Meta Marketing API | 광고 성과 |
| TikTok | TikTok Marketing API | 광고 성과 |
| 커머스 | Shopify 등 | 상품/매출 데이터 |

API 공급자는 지속적으로 바뀔 수 있으므로 **특정 회사에 강하게 종속되지 않는 구조**를 설계한다.

---

## 6.3 AI Routing 전략

모든 작업에 최고가 모델을 사용하지 않는다.

### Low-cost Model
사용:
- 광고 태깅
- 카테고리 분류
- CTA 추출
- Hook 추출
- 간단 요약

### Mid-tier Model
사용:
- 광고 비교
- 패턴 분석
- Creative Brief

### High-end Model
사용:
- 주간 전략
- 복잡한 성과 해석
- 핵심 캠페인 기획

이를 통해 품질을 유지하면서 원가를 줄인다.

---

# 7. API 원가와 수익성 설계

## 7.1 가장 중요한 리스크

사용자가 직접 사용하는 SaaS이기 때문에 무제한 생성 구조는 위험하다.

예:

```text
월 구독료 500,000원

고객 A → 영상 10개
고객 B → 영상 300개

동일 가격
```

고객 B의 AI 사용 원가가 구독료를 넘을 수 있다.

---

## 7.2 추천 가격 구조

### 기본 구조

**Base Subscription + Credits + Overage**

예시:

| 플랜 | 월 구독료 예시 | 주요 기능 |
|---|---:|---|
| Starter | 390,000원 | 경쟁사 5개, 분석 중심 |
| Growth | 790,000원 | 경쟁사 10개, Creative 생성 |
| Pro | 1,490,000원 | 경쟁사 20개, 다량 생성 |
| Agency | 별도 협의 | 다계정/다브랜드 |

가격은 실제 MVP 사용량과 고객 인터뷰 후 확정한다.

---

## 7.3 Credit 구조 예시

```text
Growth Plan
월 10,000 Credits

광고 텍스트 분석    1~2 credits
카피 생성           1 credit
이미지 생성         20~50 credits
영상 생성           200~500 credits
고급 전략 분석      10~30 credits
```

실제 credit 비율은 각 API의 실사용 원가 데이터를 기반으로 조정한다.

---

## 7.4 상품을 두 개로 분리하는 방법

### Core Intelligence SaaS
포함:
- 경쟁사 분석
- 자사 성과 분석
- Creative Recommendation
- Script / Copy

### Creative Credits
별도:
- 이미지
- 영상
- Voice
- 대량 variation

이 구조는 원가 변동성이 큰 생성형 기능을 별도로 관리할 수 있다는 장점이 있다.

---

## 7.5 원가 목표

### 권장 목표

**AI + Infra COGS / Revenue ≤ 20~30%**

| 원가율 | 판단 |
|---:|---|
| 10% 이하 | 매우 우수 |
| 10~20% | 우수 |
| 20~30% | 관리 가능 |
| 30~40% | 개선 필요 |
| 40% 이상 | 위험 |

---

## 7.6 고객당 Unit Economics 예시

월 99만원 플랜을 가정한 목표치 예시:

| 항목 | 월 목표 원가 |
|---|---:|
| LLM | 2~5만원 |
| 이미지 API | 3~8만원 |
| 영상 API | 5~15만원 |
| 서버/DB | 2~5만원 |
| 데이터 수집 | 3~10만원 |
| 기타 | 2~5만원 |
| 총 변동원가 | 약 17~48만원 |

이 수치는 확정 원가가 아니라 **초기 사업 모델링용 범위**다.

실제 API 단가와 고객별 사용량을 30~60일 동안 수집하여 재설계해야 한다.

---

# 8. API 비용 절감 전략

## 8.1 분석 결과 재사용

같은 경쟁사 광고를 고객마다 다시 분석하지 않는다.

```text
경쟁사 광고
   ↓
최초 AI 분석
   ↓
Shared Creative DB
   ↓
고객 A / B / C가 재사용
```

API 비용은 한 번 지불하지만 여러 고객에게 활용 가능하다.

---

## 8.2 사전 분석

사용자가 버튼을 누를 때마다 API를 호출하는 대신 주요 시장 데이터를 미리 처리한다.

```text
Crawler / Data Source
        ↓
Raw Creative
        ↓
Batch AI Processing
        ↓
Structured Database
        ↓
사용자 Query
```

---

## 8.3 데이터 구조화

AI 결과를 텍스트 보고서로만 저장하지 않는다.

예:

```json
{
  "hook_type": "problem",
  "format": "ugc",
  "offer": "20_percent_discount",
  "duration": 18,
  "cta": "shop_now"
}
```

구조화하면 매번 LLM에게 다시 읽힐 필요가 줄어든다.

---

## 8.4 생성 제한

특히 영상은 무제한 제공하지 않는다.

추천 정책:
- Plan별 월 영상 credit
- Preview와 Final 분리
- 저비용 Draft 모델 우선
- 고해상도 export에 추가 credit

---

# 9. 수익모델

## 9.1 1단계 — Service-led SaaS

초기에는 사람이 일부 운영한다.

예:

**월 50~150만원**

제공:
- 경쟁사 분석
- 주간 Insight
- 신규 Creative 아이디어
- Script/Copy
- 자사 광고 분석
- 다음 주 테스트 제안

목적은 소프트웨어 매출보다 **고객 문제와 반복 업무를 학습하는 것**이다.

---

## 9.2 2단계 — B2B SaaS

고객이 직접 로그인하여 사용.

매출:

```text
Monthly Subscription
+
Creative Credits
```

---

## 9.3 3단계 — Agency / Enterprise

광고대행사는 한 고객이 여러 광고계정을 사용한다.

예:

```text
Agency Base Fee
+
Brand Seat
+
Usage Credits
```

대행사 1곳 확보로 다수 브랜드 데이터와 매출을 동시에 확보할 수 있다.

---

## 9.4 장기 옵션

- 광고비 연동 요금
- 성과 기반 수수료
- Enterprise API
- Creative Intelligence Data
- Benchmark Report
- Managed AI Marketing Service

---

# 10. 경쟁우위와 해자

## 10.1 약한 해자

- Prompt
- OpenAI API
- 이미지 생성 기능
- 카피 생성 기능

누구나 빠르게 복제 가능하다.

---

## 10.2 강한 해자

### ① Creative Database

수많은 시장 광고를 다음과 같이 구조화.

```text
Creative
+
Hook
+
Offer
+
Category
+
Format
+
Product
+
Duration
+
Landing Page
```

### ② First-party Performance Data

고객사가 직접 연결한 실제 성과.

```text
Creative
+
Spend
+
CTR
+
CPA
+
CVR
+
ROAS
```

### ③ Recommendation Dataset

가장 중요.

```text
추천한 실험
        ↓
실제로 집행 여부
        ↓
성과
        ↓
다음 추천
```

시간이 지날수록:

> 어떤 산업의 어떤 브랜드가 어떤 Hook/Format/Offer 조합에서 높은 성과를 보이는가?

를 더 정확히 판단할 수 있다.

---

# 11. 주요 리스크와 대응 전략

| 리스크 | 내용 | 대응 |
|---|---|---|
| AI API 비용 | Heavy user가 원가 급증 | Credit + Overage |
| 영상 생성 비용 | 생성 실패/재시도 비용 | Draft/Preview 구조 |
| 특정 AI 공급자 종속 | 가격/성능 변화 | Multi-model routing |
| Meta/TikTok 정책 변화 | API 접근 제한 가능 | 데이터 소스 다변화 |
| 경쟁사 성과 추정 오류 | 경쟁사의 실제 ROAS 확인 불가 | Signal로 명시 |
| 콘텐츠 동질화 | 경쟁사 Copy 위험 | Pattern → Brand Adaptation |
| 광고 자동화 손실 | AI 집행 오류 | 초기 Human Approval |
| 개인정보/광고 데이터 | 보안 이슈 | 최소 권한/암호화/분리 저장 |
| 기능 과다 | MVP 개발 지연 | Observe→Learn→Recommend 순서 |
| 대형 플랫폼 기능 흡수 | Meta/Google 자체 AI 강화 | Cross-channel Intelligence 및 고객 고유 데이터 중심 |

---

# 12. 90일 실행 로드맵

## Phase 1 — Day 1~30: 문제 검증

### 목표
고객이 실제로 돈을 지불하는 문제를 찾는다.

### 실행

#### 1주차
- 타깃 업종 1개 선정
- 후보 브랜드 100곳 리스트업
- 마케팅 담당자 20명 인터뷰
- 현재 광고 제작 프로세스 파악

질문 예시:
- 일주일에 광고 소재를 몇 개 만드나요?
- 경쟁사 광고는 어떻게 조사하나요?
- 가장 시간이 많이 걸리는 작업은?
- 광고 성과를 보고 다음 소재를 누가 결정하나요?
- 현재 사용하는 SaaS는?
- 광고대행사 비용은?
- 이 과정을 자동화하면 얼마까지 낼 의향이 있나요?

#### 2~4주차
5~10개 브랜드에 수작업 서비스 제공.

제공물:
- 경쟁사 신규 광고
- 주간 Trend
- 광고 패턴 분석
- 다음 Creative 10개
- Script/Copy
- 간단 Performance Review

### 성공 기준
- 5개 이상 실제 사용
- 3개 이상 유료 전환
- 매주 반복 사용 발생

---

## Phase 2 — Day 31~60: Concierge MVP → Software MVP

### 목표
가장 반복적인 업무 1~2개를 자동화한다.

### 개발 우선순위

1. 브랜드/경쟁사 등록
2. 광고 데이터 저장
3. 자동 태깅
4. Creative Library
5. Weekly Insight
6. Next Creative Recommendation

### 하지 않을 것

- 완벽한 영상 생성
- 광고 자동집행
- 모든 채널 지원
- Enterprise 기능

---

## Phase 3 — Day 61~90: Performance 연결

### 목표
시장 정보와 고객 성과 데이터를 연결한다.

### 실행

- Meta Ads API 연결
- Creative ID와 광고 성과 연결
- 주간 Performance Report
- 다음 Test Recommendation
- 고객별 AI 원가 추적
- Credit System 테스트

### Aha Moment 목표

사용자가 다음과 같은 답을 받는 순간:

> “시장에서 할인형 광고가 증가하고 있지만, 귀사의 데이터에서는 후기형 UGC가 평균 ROAS가 더 높습니다. 다음 주에는 후기형 5개를 우선 테스트하세요.”

---

# 13. 단계별 실행계획

| 단계 | 핵심 질문 | 해야 할 일 | 산출물 |
|---|---|---|---|
| 1 | 누가 가장 아픈가? | 고객 인터뷰 | ICP |
| 2 | 무엇이 가장 반복적인가? | 업무 Shadowing | Workflow Map |
| 3 | 돈을 내는가? | 수작업 서비스 판매 | Paid Pilot |
| 4 | 무엇부터 자동화할까? | 반복 업무 시간 측정 | MVP Scope |
| 5 | 추천이 유용한가? | Weekly Creative Test | Recommendation Data |
| 6 | 실제 성과와 연결되는가? | Meta API | Performance DB |
| 7 | 원가가 감당되는가? | API Cost Logging | Unit Economics |
| 8 | 확장 가능한가? | 셀프서브 SaaS | Subscription Product |

---

# 14. 핵심 KPI

## 14.1 Product KPI

| KPI | 초기 목표 |
|---|---:|
| Weekly Active Brand | 60%+ |
| 주간 Creative Recommendation | 브랜드당 10개+ |
| 추천 Creative 열람률 | 70%+ |
| 추천 Creative 실제 사용률 | 30~40%+ |
| 추천 실험 실행률 | 30%+ |
| 8주 Retention | 60%+ |
| 제작 시간 절감 | 50~70%+ |

---

## 14.2 Performance KPI

| KPI | 목표 |
|---|---:|
| CPA 개선 | 10%+ |
| CTR 개선 | 10%+ |
| Creative Winner 발견 속도 | 지속 단축 |
| Creative Test 수 | 증가 |
| Time-to-New-Creative | 감소 |

주의:

제품의 초기 가치는 반드시 ROAS 개선 하나로만 정의할 필요는 없다.

**광고 소재 생산량 증가 + 테스트 속도 증가 + 마케터 시간 절감**도 강한 ROI가 될 수 있다.

---

## 14.3 Business KPI

| KPI | 의미 |
|---|---|
| MRR | 월 반복매출 |
| ARPA | 고객사당 평균매출 |
| Logo Churn | 고객사 이탈 |
| CAC | 기업 고객 획득비 |
| CAC Payback | 영업비 회수기간 |
| Gross Margin | SaaS 경제성 |
| AI Cost / Revenue | AI 원가 효율 |
| Net Revenue Retention | 확장 매출 |

### 핵심 Cost KPI

> **AI + Infrastructure Cost / Revenue**

초기부터 고객별로 반드시 추적한다.

---

# 15. MVP 가격 검증안

초기 테스트용으로 다음 3개 상품을 동시에 제시할 수 있다.

## Pilot A — Intelligence

**월 49만원**

- 경쟁사 5개
- 경쟁 광고 분석
- 주간 Insight
- Creative Recommendation
- Script/Copy

## Pilot B — Growth

**월 99만원**

- 경쟁사 10개
- 자사 광고 성과 분석
- Creative Recommendation
- 이미지 생성 Credit
- 일부 영상 Credit

## Pilot C — Managed

**월 199만원+**

- 전략 리뷰
- Creative 기획
- 콘텐츠 생성
- Performance 분석
- 주간 마케팅 운영

목표는 어떤 가격이 잘 팔리는지를 확인하는 것이 아니라:

> **고객이 어떤 결과에 가장 큰 비용을 지불하는지 확인하는 것.**

---

# 16. 기술 개발 전 검증할 핵심 가설

## 가설 1
커머스 마케터는 경쟁사 광고 분석에 충분히 많은 시간을 쓴다.

## 가설 2
경쟁사 분석 결과만으로는 부족하고, 다음 Creative Recommendation에 더 높은 가치를 느낀다.

## 가설 3
고객은 AI 생성 횟수보다 **성과 좋은 Creative를 더 빨리 찾는 것**에 돈을 낸다.

## 가설 4
고객은 AI가 직접 광고를 집행하는 것보다 초기에는 승인 후 집행을 선호한다.

## 가설 5
월 50~150만원 수준에서 마케터 업무 시간 절감 효과가 충분하면 구매 의향이 있다.

## 가설 6
공통 경쟁사 데이터의 재사용으로 고객 증가 대비 AI 분석 원가는 비례해서 증가하지 않는다.

---

# 17. 초기 영업 전략

## 17.1 영업 메시지

기능을 팔지 않는다.

### 나쁜 메시지

> “AI로 광고 소재를 생성하는 SaaS입니다.”

### 추천 메시지

> **“매주 경쟁사 광고와 귀사의 Meta 성과를 분석해서 다음에 테스트할 광고 소재를 10개씩 제안해드립니다.”**

또는:

> **“마케터가 매주 하던 경쟁사 리서치와 다음 광고 기획 업무를 자동화합니다.”**

---

## 17.2 초기 고객 확보 방식

1. 특정 업종 브랜드 100개 선정
2. 브랜드 광고 직접 분석
3. 해당 회사용 1페이지 샘플 리포트 제작
4. 대표/CMO/마케팅팀에 전달
5. 2주 무료 Pilot 또는 저가 Paid Pilot
6. 매주 실제 광고 회의에 사용하게 함
7. 실제 제작/집행 여부 추적
8. 유료 전환

---

## 17.3 강력한 세일즈 샘플

영업 전에 고객의 경쟁사 3~5개를 분석한다.

예:

```text
최근 경쟁사 5곳의 광고 132개 분석

주요 변화:
1. UGC 비중 증가
2. 15초 이하 영상 증가
3. 할인보다 효능 Hook 증가

귀사 광고와 비교:
- 귀사는 제품 설명형 비중이 높음
- 후기형 Creative가 상대적으로 부족

추천:
다음 테스트 5개
```

고객에게 자신의 브랜드에 대한 결과를 먼저 보여주면 SaaS 화면 설명보다 훨씬 설득력이 높다.

---

# 18. 사업 확장 로드맵

```text
Phase 1
Creative Intelligence
        ↓
Phase 2
Performance Intelligence
        ↓
Phase 3
Creative Recommendation
        ↓
Phase 4
Creative Generation
        ↓
Phase 5
Campaign Execution
        ↓
Phase 6
Autonomous Marketing Agent
```

장기적으로:

```text
사용자:
"이번 달 신제품 매출 1억원이 목표야."

AI:
시장 분석
↓
Creative 전략
↓
광고 생성
↓
Budget Allocation
↓
Campaign Launch
↓
Performance Monitoring
↓
Creative Iteration
↓
목표 최적화
```

까지 발전할 수 있다.

---

# 19. 최종 사업 정의

이 사업을 단순하게 정의하면:

> **AI를 활용해 광고를 만들어주는 서비스**

가 아니다.

보다 정확한 정의는:

> **커머스 기업의 반복적인 퍼포먼스 마케팅 의사결정과 Creative 실험 과정을 자동화하는 B2B AI SaaS**

이다.

### 고객이 사는 것

**AI 생성 횟수**가 아니라,

- 마케터 시간 절감
- 콘텐츠 생산속도 증가
- 광고 테스트 수 증가
- Winner Creative 발견 속도 향상
- 광고 성과 개선

이다.

### 회사가 쌓아야 하는 자산

1. Workflow
2. Creative Database
3. First-party Performance Data
4. Recommendation Dataset
5. 고객별 AI 원가 최적화 기술

### 초기 전략 한 줄

> **처음부터 모든 것을 자동화하지 말고, 사람이 직접 서비스를 제공하면서 고객이 매주 돈을 내고 반복해서 사용하는 “다음 광고 추천” 업무를 먼저 발견한 뒤 소프트웨어로 전환한다.**

---

# 20. 즉시 실행 체크리스트

## 이번 주

- [ ] 첫 타깃 업종 1개 선정
- [ ] 브랜드 100개 리스트 작성
- [ ] 마케팅 담당자 인터뷰 후보 20명
- [ ] 인터뷰 질문 작성
- [ ] 경쟁사 광고 샘플 분석 포맷 제작
- [ ] 1페이지 Weekly Creative Report 제작

## 30일 내

- [ ] 인터뷰 20건
- [ ] Pilot 고객 5곳
- [ ] 유료 고객 3곳 이상
- [ ] 실제 주간 업무시간 측정
- [ ] 고객별 AI/API 원가 기록
- [ ] 가장 많이 반복된 업무 3개 도출

## 90일 내

- [ ] 경쟁사 Creative DB
- [ ] 자동 광고 태깅
- [ ] Meta Performance 연결
- [ ] Next Creative Recommendation
- [ ] 고객별 Credit/원가 관리
- [ ] 10개 이상 반복 사용 브랜드
- [ ] 유료 Retention 검증

---

## 핵심 의사결정 기준

향후 모든 기능 개발은 다음 질문을 통과해야 한다.

> **“이 기능이 고객이 다음으로 어떤 광고를 테스트해야 할지 더 빠르고 정확하게 결정하도록 도와주는가?”**

YES라면 우선순위를 높인다.

NO라면 초기에는 만들지 않는다.
