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

---

## ADR-012 — Meta Manual Research and TikTok Automated Collection

**Status:** Superseded by ADR-014

### Decision

- Meta 공식 `ads_archive` API와 비공식 화면 스크래핑을 베트남 일반 상업 광고 자동 수집 경로로 사용하지 않는다.
- Meta 광고는 Web 작업 공간에서 공식 광고 라이브러리로 이동해 사용자가 직접 조사한다. 경쟁 브랜드명과 업종을 검색어로 전달하는 빠른 링크를 제공한다.
- 필요한 Meta 광고는 기존 Creative 직접 등록 경로로 원본 주소와 문구를 저장하고 분석한다.
- 자동 수집 source의 신규 생성과 실행은 TikTok만 허용한다.
- 기존 Meta source 데이터는 삭제하지 않지만 API sync와 scheduler에서 실행하지 않는다. 이미 대기 중인 Meta Job은 `PLATFORM_MANUAL_ONLY`로 종료하고 source를 일시중지한다.

### Reason

- Meta 공식 API는 전 세계 정치·사회 이슈 광고에는 접근 가능하지만 베트남 일반 상업 광고 전체 접근을 보장하지 않는다.
- 제한된 공식 API 범위를 외부 계약형 수집이나 화면 스크래핑으로 우회하면 제품 안정성, 약관 검토, 데이터 품질 비용이 커진다.
- Meta 공식 Web은 조사 출처를 명확히 유지하고, TikTok 자동화와 수동 Meta 조사의 차이를 사용자에게 투명하게 보여준다.
- 기존 source를 보존하면 사용자 데이터 유실 없이 향후 공식 접근 범위가 바뀔 때 재검토할 수 있다.

### Revisit when

- Meta가 베트남 일반 상업 광고에 대한 공식적이고 안정적인 API 접근을 제공할 때
- Meta 광고 자동 수집이 Pilot 운영에 필수라는 검증된 요구가 생길 때

### References

- [Meta Ads Library 소개](https://about.fb.com/news/2019/03/a-better-way-to-learn-about-ads/)
- [Meta 공식 Ad Library API 예제 저장소](https://github.com/facebookresearch/Ad-Library-API-Script-Repository)
- [Meta Ads Library](https://www.facebook.com/ads/library/)

---

## ADR-013 — Apify Candidate for Vietnam TikTok Top Ads

**Status:** Proposed — adapter implemented, business approval and paid smoke pending

### Decision

- TikTok 공식 Commercial Content API는 베트남 광고를 지원하지 않으므로 현재 production provider로 사용하지 않는다.
- 베트남 Creative Center Top Ads, 키워드, 업종, 기간 필터를 제공하는 Apify Actor를 첫 계약형 후보로 둔다.
- 외부 Actor 호출은 `AdLibraryCollector` 뒤의 Worker adapter로 격리하고 API token은 Worker에만 주입한다.
- 호출마다 최대 결과 수와 최대 USD 과금을 제한한다.
- 외부 응답은 Pydantic으로 검증하고 영구 Creative Center URL과 분석에 필요한 최소 메타데이터만 저장한다.
- 이 경로는 경쟁사의 전체 광고가 아닌 TikTok Creative Center의 공개 Top Ads 표본임을 UI에 표시한다.

### Reason

- TikTok 공식 지원 국가 목록에 베트남이 없다.
- 후보 Actor는 `VN`, 7/30/180일, 키워드·업종 필터와 Creative Center 영구 URL을 제공한다.
- Apify API는 bearer token, 비동기 Actor 실행, 결과 건수 및 최대 과금 제한을 제공한다.
- Actor ID를 config로 분리해 품질이나 약관 검토 결과에 따라 다른 구현으로 교체할 수 있다.

### Approval gates

- Apify와 Actor 개발자의 이용약관·공개 데이터 재사용·보관 범위 승인
- Top Ads 표본이 Pilot의 경쟁사·업종 조사 목적에 충분한지 확인
- 예상 브랜드 수, 동기화 주기, 월 최대 예산 확정
- Worker용 Apify API token 발급 후 VN 광고 1건 유료 smoke
- 베트남 브랜드명과 업종 키워드 표본으로 검색 정확도 검증

### References

- [TikTok Commercial Content API 지원 국가](https://developers.tiktok.com/docs/en/commercial-content-api-supported-countries)
- [TikTok Commercial Content API](https://developers.tiktok.com/products/commercial-content-api)
- [Apify Actor API](https://docs.apify.com/api/v2)
- [TikTok Creative Center Top Ads Actor 후보](https://apify.com/khadinakbar/tiktok-ads-scraper)

---

## ADR-014 — Apify Automation for Meta and TikTok

**Status:** Accepted — production token and paid smoke pending

### Decision

- Meta와 TikTok 공개 광고 수집을 `AdLibraryCollector` 뒤의 플랫폼별 Apify Actor adapter로 자동화한다.
- Meta는 Apify가 유지보수하는 `apify/facebook-ads-scraper`에 국가 `VN`, 활성 광고, 경쟁사명 또는 업종 키워드가 포함된 Meta 광고 라이브러리 URL을 전달한다.
- TikTok은 Creative Center Top Ads 표본 adapter를 유지한다.
- API token은 Worker에만 주입하고, 플랫폼별 결과 수와 USD 과금 상한을 config로 분리한다.
- Actor 응답은 Pydantic으로 검증하고 영구 광고 URL, 문구와 최소 메타데이터만 저장한다. 임시 미디어 URL과 불필요한 원본 payload는 저장하지 않는다.
- 공식 Meta 광고 라이브러리와 TikTok Creative Center 링크는 사용자가 수집 결과를 직접 검증하는 보조 경로로 유지한다.

### Reason

- Meta 공식 API만으로 베트남 일반 상업 광고 자동 수집 범위를 충족하기 어렵다.
- Apify의 공식 유지보수 Actor는 페이지 또는 광고 라이브러리 URL, 국가·상태·미디어 필터와 결과 제한을 제공한다.
- 외부 Actor 종속성을 adapter와 config로 격리하면 구조 변경, 품질 저하 또는 약관 변경 시 provider를 교체할 수 있다.

### Operational gates

- Worker용 Apify API token 발급
- Meta와 TikTok 각각 VN 광고 1건의 유료 smoke 및 schema 확인
- 월 예산, 실행 주기, 보관 기간 확정
- Actor 및 Meta/TikTok 공개 데이터 이용약관 검토

### References

- [Apify Facebook Ads Library Scraper](https://apify.com/apify/facebook-ads-scraper)
- [Apify Actor API](https://docs.apify.com/api/v2)
- [Meta Ads Library](https://www.facebook.com/ads/library/)

---

## ADR-015 — Service-managed $40 Subscription and Provider Credentials

**Status:** Proposed — implementation complete, live Stripe/Apify/OpenAI smoke pending

### Decision

- 초기 셀프서비스 플랜은 Organization당 월 `$40 USD`로 제공한다.
- 고객은 Stripe hosted Checkout에서 결제하지만 Apify/OpenAI API key를 직접 입력하지 않는다.
- Apify/OpenAI 계정과 secret은 서비스가 중앙 관리하고, 사용량·credit·Job은 Organization별로 추적한다.
- 월 제공량은 provider credit `$15`, AI 분석 200회, 자동 수집 50회, 브랜드 1개, 경쟁 브랜드 5개로 시작한다.
- 결제 domain은 provider-independent interface 뒤에 두고 Stripe를 첫 운영 adapter로 사용한다.
- 비용 Job은 실행 전 credit reservation, 성공 후 settlement, 실패 시 release를 기록한다.
- BYOK는 초기 플랜에 포함하지 않고 향후 Agency/Enterprise 요구가 확인될 때 재검토한다.

### Reason

- 고객에게 외부 provider 계정 발급과 secret 관리를 요구하면 onboarding과 보안 책임이 커진다.
- Apify 기본 구독과 provider 계정을 Organization마다 중복 구매하지 않고 서비스 전체에서 공유해야 초기 단가를 통제할 수 있다.
- 구독 매출 전체를 provider 비용으로 허용하지 않고 Organization당 변동비를 `$15` 이하로 제한해야 인프라·결제·지원 비용을 확보할 수 있다.

### Operational gates

- Stripe 사업자 계정, 월 `$40 USD` recurring Price, webhook signing secret 발급
- 환불·세금·통화·연체·해지 정책 확정
- Apify 약관·월 예산 승인 및 Meta/TikTok 유료 smoke
- OpenAI project key 발급 및 실제 분석 비용 표본 측정
