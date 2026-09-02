# Open Questions

Codex/개발 중 제품 결정이 필요한 사항은 임의 확장 구현하지 말고 이 문서에 기록한다.

## Product
- [ ] 첫 Pilot Vertical은 무엇인가? (뷰티/패션/식품 등)
- [ ] 한 Organization이 여러 Brand를 운영하는 것이 초기부터 필수인가?
- [x] 수동 입력은 fallback으로 유지하고 자동 수집 PoC를 우선한다. (`ADR-011`)
- [x] 베트남 Meta 상업 광고도 Apify로 자동 수집하고 공식 광고 라이브러리를 검증 경로로 유지한다. (`ADR-014`)
- [x] 초기 운영은 주 1회, Organization당 provider credit `$15`, 플랫폼별 `$0.25/run` 상한으로 제한한다. (`ADR-015`)
- [ ] 수집 Creative와 최소 raw payload의 데이터 보관 기간은 얼마로 할 것인가?
- [ ] Pilot은 경쟁사 전체 광고가 아니라 Creative Center Top Ads 표본으로 충분한가?
- [ ] 첫 Pilot 업종과 베트남어/영어 핵심 검색어는 무엇인가?
- [ ] Creative 분석 결과에서 실제 고객에게 가장 중요한 5개 필드는 무엇인가?

## Auth
- [x] deterministic dev auth adapter를 병행한다. production은 Supabase adapter만 허용한다. (`ADR-009`)
- [ ] 초대 기능은 Phase 1에 필요한지, 단일 owner부터 시작할지?

## Creative
- [ ] asset upload를 Phase 2에 포함할지, URL/text metadata부터 시작할지?
- [x] 1차 중복 제거는 tenant/source/source_external_id를 사용한다. 미디어 fingerprint는 추후 확장한다. (`ADR-011`)

## AI
- [x] 첫 실제 AI provider는 OpenAI Responses API로 선택한다. (`ADR-010`)
- [x] Phase 3은 text/metadata 분석만 포함하고 실제 image input은 보류한다. (`ADR-010`)
- [ ] 분석 schema의 confidence를 어떻게 정의할지?

## Infra
- [ ] production/staging hosting provider
- [ ] managed PostgreSQL/Supabase 운영 방식
- [ ] error monitoring service 선택

## Billing
- [x] 초기 셀프서비스 가격은 Organization당 월 `$40 USD`로 한다. (`ADR-015`)
- [x] 고객 BYOK 없이 서비스가 Apify/OpenAI secret을 중앙 관리한다. (`ADR-015`)
- [ ] Stripe 사업자 계정과 월 `$40` recurring Price 발급
- [ ] 세금계산·부가세, 환불, 연체, 해지 효력 시점 정책
- [ ] provider credit 초과 시 차단만 할지 overage/상위 플랜을 제공할지

결정한 항목은 `docs/DECISIONS.md`에 ADR로 옮긴다.
