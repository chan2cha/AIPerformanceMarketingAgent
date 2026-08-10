# Open Questions

Codex/개발 중 제품 결정이 필요한 사항은 임의 확장 구현하지 말고 이 문서에 기록한다.

## Product
- [ ] 첫 Pilot Vertical은 무엇인가? (뷰티/패션/식품 등)
- [ ] 한 Organization이 여러 Brand를 운영하는 것이 초기부터 필수인가?
- [ ] 경쟁사 Creative 수집을 MVP에서 수동 입력으로 시작할지, 데이터 수집 PoC를 병행할지?
- [ ] Creative 분석 결과에서 실제 고객에게 가장 중요한 5개 필드는 무엇인가?

## Auth
- [ ] 초기 local development에서 Supabase Auth를 즉시 연결할지, deterministic dev auth adapter를 병행할지?
- [ ] 초대 기능은 Phase 1에 필요한지, 단일 owner부터 시작할지?

## Creative
- [ ] asset upload를 Phase 2에 포함할지, URL/text metadata부터 시작할지?
- [ ] 동일 Creative deduplication fingerprint 규칙은 무엇인가?

## AI
- [ ] 첫 실제 AI provider는 어떤 공급자로 할지?
- [ ] 이미지 Creative 분석 시 실제 image input을 Phase 3에 포함할지?
- [ ] 분석 schema의 confidence를 어떻게 정의할지?

## Infra
- [ ] production/staging hosting provider
- [ ] managed PostgreSQL/Supabase 운영 방식
- [ ] error monitoring service 선택

결정한 항목은 `docs/DECISIONS.md`에 ADR로 옮긴다.
