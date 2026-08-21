# Open Questions

Codex/개발 중 제품 결정이 필요한 사항은 임의 확장 구현하지 말고 이 문서에 기록한다.

## Product
- [ ] 첫 Pilot Vertical은 무엇인가? (뷰티/패션/식품 등)
- [ ] 한 Organization이 여러 Brand를 운영하는 것이 초기부터 필수인가?
- [x] 수동 입력은 fallback으로 유지하고 자동 수집 PoC를 우선한다. (`ADR-011`)
- [ ] 베트남 Meta/TikTok 상업 광고의 production 수집에 사용할 공식·계약형 provider는 무엇인가?
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

결정한 항목은 `docs/DECISIONS.md`에 ADR로 옮긴다.
