"use client";

import { FormEvent, ReactNode, useRef, useState } from "react";
import { ApiError, apiRequest } from "./api";
import type { BillingSummary, Brand, CollectionSource, Competitor, Creative, CreativeDetail, Job, Me, Organization, UsageSummary } from "./types";

type LoadState = "idle" | "loading" | "ready";
type WorkspaceStep = "billing" | "brand" | "market" | "collection" | "analysis";
const steps: { id: WorkspaceStep; label: string; description: string }[] = [
  { id: "billing", label: "플랜", description: "결제와 제공량" },
  { id: "brand", label: "브랜드", description: "분석 기준 만들기" },
  { id: "market", label: "시장", description: "경쟁사 정하기" },
  { id: "collection", label: "자동 수집", description: "광고 채널 연결" },
  { id: "analysis", label: "분석", description: "소재와 인사이트" },
];
const ownershipLabel = { own: "우리 브랜드", competitor: "경쟁 브랜드", market: "시장 사례" } as const;
const mediaLabel = { image: "이미지", video: "영상", carousel: "여러 장", text: "텍스트" } as const;
const platformLabel = { meta_ad_library: "Meta 광고 라이브러리", tiktok_creative_center: "TikTok 광고 라이브러리" } as const;
const jobStatusLabel = { queued: "분석 준비 중", processing: "AI가 분석 중", completed: "분석 완료", failed: "분석 실패", cancelled: "분석 취소됨" } as const;
const collectionStatusLabel = { queued: "수집 준비 중", processing: "광고 수집 중", completed: "수집 완료", failed: "수집 실패", cancelled: "수집 취소됨" } as const;
const value = (form: FormData, key: string) => String(form.get(key) ?? "").trim();
const date = (input: string) => new Intl.DateTimeFormat("ko-KR", { month: "short", day: "numeric" }).format(new Date(input));
const message = (error: unknown) => error instanceof ApiError ? error.message : "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.";
const metaLibraryUrl = (query?: string | null) => {
  const params = new URLSearchParams({ active_status: "active", ad_type: "all", country: "VN", media_type: "all" });
  if (query?.trim()) {
    params.set("q", query.trim());
    params.set("search_type", "keyword_unordered");
  }
  return `https://www.facebook.com/ads/library/?${params.toString()}`;
};
const tiktokLibraryUrl = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en?region=VN";

export function MarketingWorkspace({ initialApiHealthy }: { initialApiHealthy: boolean }) {
  const [subjectInput, setSubjectInput] = useState("demo-owner");
  const [subject, setSubject] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [brands, setBrands] = useState<Brand[]>([]);
  const [brandId, setBrandId] = useState("");
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [collectionSources, setCollectionSources] = useState<CollectionSource[]>([]);
  const [creatives, setCreatives] = useState<Creative[]>([]);
  const [creative, setCreative] = useState<CreativeDetail | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [billing, setBilling] = useState<BillingSummary | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [collectionJob, setCollectionJob] = useState<Job | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [error, setError] = useState("");
  const [openForm, setOpenForm] = useState<"org" | "brand" | "competitor" | "creative" | "source" | null>(null);
  const [ownershipFilter, setOwnershipFilter] = useState("");
  const [mediaFilter, setMediaFilter] = useState("");
  const [activeStep, setActiveStep] = useState<WorkspaceStep>("billing");
  const tenantVersion = useRef(0);

  const activeBrand = brands.find((item) => item.id === brandId);

  async function fetchUsage(user: string, orgId: string, version: number) {
    const result = await apiRequest<UsageSummary>(`/api/v1/organizations/${orgId}/usage`, user);
    if (tenantVersion.current === version) setUsage(result);
  }

  async function fetchBilling(user: string, orgId: string, version: number) {
    const result = await apiRequest<BillingSummary>(`/api/v1/organizations/${orgId}/billing`, user);
    if (tenantVersion.current === version) setBilling(result);
  }

  async function loadBrand(user: string, nextId: string, version: number, ownership = ownershipFilter, media = mediaFilter) {
    setBrandId(nextId); setCompetitors([]); setCollectionSources([]); setCreatives([]); setCreative(null); setJob(null); setError("");
    if (!nextId) return;
    setLoadState("loading");
    try {
      const query = new URLSearchParams();
      if (ownership) query.set("ownership_type", ownership);
      if (media) query.set("media_type", media);
      const suffix = query.size ? `?${query}` : "";
      const [rivals, items, sources] = await Promise.all([
        apiRequest<Competitor[]>(`/api/v1/brands/${nextId}/competitors`, user),
        apiRequest<Creative[]>(`/api/v1/brands/${nextId}/creatives${suffix}`, user),
        apiRequest<CollectionSource[]>(`/api/v1/brands/${nextId}/collection-sources`, user),
      ]);
      if (tenantVersion.current !== version) return;
      setCompetitors(rivals); setCollectionSources(sources); setCreatives(items); setLoadState("ready");
    } catch (caught) {
      if (tenantVersion.current === version) { setError(message(caught)); setLoadState("ready"); }
    }
  }

  async function loadOrganization(user: string, orgId: string) {
    const version = ++tenantVersion.current;
    // Clear tenant-owned state before issuing requests so stale data is never rendered.
    setOrganizationId(orgId); setBrandId(""); setBrands([]); setCompetitors([]); setCollectionSources([]); setCreatives([]); setCreative(null); setUsage(null); setBilling(null); setJob(null); setCollectionJob(null); setActiveStep("billing"); setError("");
    if (!orgId) return;
    setLoadState("loading");
    try {
      const [items, billingSummary] = await Promise.all([
        apiRequest<Brand[]>(`/api/v1/organizations/${orgId}/brands`, user),
        apiRequest<BillingSummary>(`/api/v1/organizations/${orgId}/billing`, user),
        fetchUsage(user, orgId, version),
      ]);
      if (tenantVersion.current !== version) return;
      setBrands(items); setBilling(billingSummary); setLoadState("ready"); setActiveStep("billing");
      if (items[0]) await loadBrand(user, items[0].id, version);
    } catch (caught) {
      if (tenantVersion.current === version) { setError(message(caught)); setLoadState("ready"); }
    }
  }

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const user = subjectInput.trim(); if (!user) return;
    setLoadState("loading"); setError("");
    try {
      const profile = await apiRequest<Me>("/api/v1/me", user);
      setSubject(user); setMe(profile); setOrganizations(profile.organizations); setLoadState("ready");
      if (profile.organizations[0]) await loadOrganization(user, profile.organizations[0].id);
    } catch (caught) { setError(message(caught)); setLoadState("ready"); }
  }

  function logout() {
    ++tenantVersion.current;
    setSubject(null); setMe(null); setOrganizations([]); setOrganizationId(""); setBrands([]); setBrandId(""); setCompetitors([]); setCollectionSources([]); setCreatives([]); setCreative(null); setUsage(null); setBilling(null); setJob(null); setCollectionJob(null); setActiveStep("billing"); setError("");
  }

  async function createOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!subject) return; const form = new FormData(event.currentTarget);
    try {
      const created = await apiRequest<Organization>("/api/v1/organizations", subject, { method: "POST", body: JSON.stringify({ name: value(form, "name") }) });
      const item = { ...created, role: "owner" as const };
      setOrganizations((current) => [...current, item]); setOpenForm(null); await loadOrganization(subject, item.id);
    } catch (caught) { setError(message(caught)); }
  }

  async function startCheckout() {
    if (!subject || !organizationId) return;
    setLoadState("loading"); setError("");
    try {
      const result = await apiRequest<{ status: "inactive" | "active"; checkout_url: string | null }>(`/api/v1/organizations/${organizationId}/billing/checkout`, subject, { method: "POST", body: JSON.stringify({}) });
      if (result.checkout_url) {
        window.location.assign(result.checkout_url);
        return;
      }
      await fetchBilling(subject, organizationId, tenantVersion.current);
      setActiveStep("brand"); setLoadState("ready");
    } catch (caught) { setError(message(caught)); setLoadState("ready"); }
  }

  async function createBrand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!subject || !organizationId) return; const form = new FormData(event.currentTarget);
    try {
      const created = await apiRequest<Brand>(`/api/v1/organizations/${organizationId}/brands`, subject, { method: "POST", body: JSON.stringify({ name: value(form, "name"), industry: value(form, "industry") || null }) });
      setBrands((current) => [...current, created]); setOpenForm(null); await loadBrand(subject, created.id, tenantVersion.current); setActiveStep("market");
    } catch (caught) { setError(message(caught)); }
  }

  async function createCompetitor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!subject || !brandId) return; const form = new FormData(event.currentTarget);
    try {
      const created = await apiRequest<Competitor>(`/api/v1/brands/${brandId}/competitors`, subject, { method: "POST", body: JSON.stringify({ name: value(form, "name"), website: value(form, "website") || null }) });
      setCompetitors((current) => [...current, created]); setOpenForm(null);
    } catch (caught) { setError(message(caught)); }
  }

  async function createCreative(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!subject || !brandId) return; const form = new FormData(event.currentTarget); const ownership = value(form, "ownership_type");
    try {
      const created = await apiRequest<Creative>(`/api/v1/brands/${brandId}/creatives`, subject, { method: "POST", body: JSON.stringify({ ownership_type: ownership, competitor_id: ownership === "competitor" ? value(form, "competitor_id") : null, media_type: value(form, "media_type"), title: value(form, "title") || null, body: value(form, "body") || null, source_url: value(form, "source_url") || null }) });
      setCreatives((current) => [created, ...current]); setOpenForm(null); await selectCreative(created.id);
    } catch (caught) { setError(message(caught)); }
  }

  async function createCollectionSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!subject || !brandId) return; const form = new FormData(event.currentTarget); const scope = value(form, "scope");
    try {
      const created = await apiRequest<CollectionSource>(`/api/v1/brands/${brandId}/collection-sources`, subject, { method: "POST", body: JSON.stringify({ platform: value(form, "platform"), scope, competitor_id: scope === "competitor" ? value(form, "competitor_id") : null, external_identifier: value(form, "external_identifier") || null, country_code: value(form, "country_code") || "VN", language_code: value(form, "language_code") || "vi", keywords: value(form, "keywords").split(",").map((item) => item.trim()).filter(Boolean), sync_interval_hours: Number(value(form, "sync_interval_hours") || 24) }) });
      setCollectionSources((current) => [...current, created]); setOpenForm(null);
    } catch (caught) { setError(message(caught)); }
  }

  async function syncCollectionSource(sourceId: string) {
    if (!subject) return; const version = tenantVersion.current; setError("");
    try {
      const accepted = await apiRequest<{ job_id: string }>(`/api/v1/collection-sources/${sourceId}/sync`, subject, { method: "POST", body: JSON.stringify({ analyze_new_creatives: true }) });
      for (let attempt = 0; attempt < 70; attempt += 1) {
        if (attempt) await new Promise((resolve) => setTimeout(resolve, 900));
        if (tenantVersion.current !== version) return;
        const current = await apiRequest<Job>(`/api/v1/jobs/${accepted.job_id}`, subject); setCollectionJob(current);
        if (current.status === "completed") { await Promise.all([loadBrand(subject, brandId, version), fetchBilling(subject, organizationId, version)]); return; }
        if (current.status === "failed" || current.status === "cancelled") return;
      }
      setError("광고 수집 시간이 예상보다 길어지고 있습니다. 잠시 후 다시 확인해 주세요.");
    } catch (caught) { setError(message(caught)); }
  }

  async function updateCollectionSource(source: CollectionSource, status: "active" | "paused") {
    if (!subject) return; setError("");
    try {
      const updated = await apiRequest<CollectionSource>(`/api/v1/collection-sources/${source.id}`, subject, { method: "PATCH", body: JSON.stringify({ status }) });
      setCollectionSources((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (caught) { setError(message(caught)); }
  }

  async function selectCreative(id: string) {
    if (!subject) return; setCreative(null); setJob(null); setLoadState("loading");
    try { setCreative(await apiRequest<CreativeDetail>(`/api/v1/creatives/${id}`, subject)); setLoadState("ready"); }
    catch (caught) { setError(message(caught)); setLoadState("ready"); }
  }

  async function refresh(ownership: string, media: string) {
    if (subject && brandId) await loadBrand(subject, brandId, tenantVersion.current, ownership, media);
  }

  async function analyze() {
    if (!subject || !creative) return; const version = tenantVersion.current; setError("");
    try {
      const accepted = await apiRequest<{ job_id: string }>(`/api/v1/creatives/${creative.id}/analyses`, subject, { method: "POST", body: JSON.stringify({ force: creative.analyses.length > 0 }) });
      for (let attempt = 0; attempt < 70; attempt += 1) {
        if (attempt) await new Promise((resolve) => setTimeout(resolve, 900));
        if (tenantVersion.current !== version) return;
        const current = await apiRequest<Job>(`/api/v1/jobs/${accepted.job_id}`, subject); setJob(current);
        if (current.status === "completed") { await Promise.all([selectCreative(creative.id), fetchUsage(subject, organizationId, version), fetchBilling(subject, organizationId, version)]); return; }
        if (current.status === "failed" || current.status === "cancelled") return;
      }
      setError("분석 시간이 예상보다 길어지고 있습니다. 잠시 후 다시 확인해 주세요.");
    } catch (caught) { setError(message(caught)); }
  }

  if (!subject) return (
    <main className="login-shell">
      <div className="login-mark">SD</div>
      <section className="login-panel">
        <p className="eyebrow">광고 소재 분석 도구</p><h1>광고의 감이<br />근거가 되는 곳.</h1>
        <p className="login-copy">우리 브랜드와 경쟁사의 광고 소재를 모아 AI로 분석하고, 다음 광고를 기획할 근거를 확인하세요.</p>
        <form onSubmit={login} className="login-form"><label htmlFor="subject">데모 사용자 이름</label><div className="input-row"><input id="subject" value={subjectInput} onChange={(event) => setSubjectInput(event.target.value)} placeholder="demo-owner" required /><button disabled={loadState === "loading"}>{loadState === "loading" ? "여는 중…" : "시작하기"}</button></div><small>개발 환경 전용 로그인입니다. 실제 비밀번호나 API 키는 입력하지 마세요.</small></form>
        {error && <p className="inline-error" role="alert">{error}</p>}
      </section>
      <div className={`api-badge ${initialApiHealthy ? "online" : "offline"}`}><span /> 서버 {initialApiHealthy ? "연결됨" : "연결 안 됨"}</div>
    </main>
  );

  const analysis = creative?.analyses[0];
  const isAnalyzing = job?.status === "queued" || job?.status === "processing";
  const canLeaveBrandStep = Boolean(brandId);
  const billingActive = billing?.status === "active" || billing?.status === "trialing";
  const billingAllowsUse = Boolean(organizationId) && (billingActive || billing?.enforcement_enabled === false);

  return (
    <main className="guided-shell">
      <header className="app-header">
        <div className="app-brand"><span>SD</span><strong>Signal Desk</strong></div>
        <div className="header-context">
          <label>
            <span>회사 / 팀</span>
            <select value={organizationId} onChange={(event) => void loadOrganization(subject, event.target.value)}>
              <option value="">선택하세요</option>
              {organizations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <div className="active-context"><span>작업 브랜드</span><strong>{activeBrand?.name || "아직 없음"}</strong></div>
        </div>
        <div className="account-menu"><span>{me?.email}</span><button onClick={logout}>로그아웃</button></div>
      </header>

      <nav className="stepper" aria-label="광고 분석 설정 단계">
        {steps.map((item, index) => {
          const disabled = item.id === "billing" ? false : item.id === "brand" ? !billingAllowsUse : !canLeaveBrandStep;
          const completed = item.id === "billing" ? billingActive : item.id === "brand" ? canLeaveBrandStep : item.id === "market" ? competitors.length > 0 : item.id === "collection" ? collectionSources.length > 0 : creatives.length > 0;
          return (
            <button
              key={item.id}
              className={`${item.id === activeStep ? "active" : ""} ${completed ? "completed" : ""}`}
              disabled={disabled}
              onClick={() => { setActiveStep(item.id); setOpenForm(null); }}
              aria-current={item.id === activeStep ? "step" : undefined}
            >
              <span>{completed ? "✓" : index + 1}</span>
              <div><strong>{item.label}</strong><small>{item.description}</small></div>
            </button>
          );
        })}
      </nav>

      {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError("")}>닫기</button></div>}

      <section className="step-screen" key={activeStep}>
        {activeStep === "billing" && (
          <>
            <ScreenHeading number="01" eyebrow="플랜과 결제" title="주 1회 시장 분석을 바로 시작하세요" description="결제 후 브랜드와 경쟁사를 설정하면 Meta·TikTok 수집과 신규 광고 AI 분석을 정해진 제공량 안에서 자동 실행합니다." />
            {!organizationId ? (
              <section className="billing-empty">
                <div><p className="eyebrow">먼저 필요한 정보</p><h3>결제할 회사 또는 팀을 만들어 주세요</h3><p>구독과 사용량은 회사 단위로 분리됩니다.</p></div>
                <button className="primary-action" onClick={() => setOpenForm(openForm === "org" ? null : "org")}>회사 / 팀 만들기</button>
                {openForm === "org" && <InlineForm onSubmit={createOrganization} fields={[{ name: "name", placeholder: "회사 또는 팀 이름" }]} />}
              </section>
            ) : billing && (
              <div className="billing-layout">
                <section className="plan-statement">
                  <div className="plan-price"><span>월</span><strong>${Number(billing.plan.monthly_price_usd).toFixed(0)}</strong><small>USD · 매월 결제</small></div>
                  <div className="plan-copy"><p className="eyebrow">{billing.plan.name}</p><h2>수집과 분석 비용을 한 플랜에서 관리합니다.</h2><p>API key를 직접 입력할 필요가 없습니다. 결제 후 브랜드·경쟁사·검색어만 설정하세요.</p></div>
                  <div className={`subscription-state state-${billing.status}`}><span />{billingActive ? "구독 활성" : billing.status === "past_due" ? "결제 확인 필요" : "결제 전"}</div>
                </section>

                <section className="allowance-table" aria-label="월 제공량">
                  <div><span>브랜드</span><strong>{billing.plan.brand_limit}개</strong><small>조직당</small></div>
                  <div><span>경쟁 브랜드</span><strong>{billing.plan.competitor_limit}개</strong><small>브랜드 기준</small></div>
                  <div><span>자동 수집</span><strong>{billing.allowance.collection_runs_used} / {billing.allowance.collection_run_limit}</strong><small>이번 결제 기간</small></div>
                  <div><span>AI 분석</span><strong>{billing.allowance.analysis_used} / {billing.allowance.analysis_limit}</strong><small>신규 소재만 차감</small></div>
                  <div><span>Provider credit</span><strong>${Number(billing.allowance.credit_remaining_usd).toFixed(2)}</strong><small>${Number(billing.plan.monthly_credit_usd).toFixed(0)} 포함</small></div>
                </section>

                <section className="provider-status">
                  <div><p className="eyebrow">서비스 연결 상태</p><h3>키는 운영 환경에서만 관리합니다</h3></div>
                  <ProviderState label="결제" ready={billing.provider_readiness.billing} />
                  <ProviderState label="광고 수집" ready={billing.provider_readiness.apify} />
                  <ProviderState label="AI 분석" ready={billing.provider_readiness.openai} />
                </section>

                <footer className="billing-actions">
                  <p>{billingActive ? "결제가 확인되었습니다. 브랜드 정보를 설정해 주세요." : billing.provider_readiness.billing ? "결제 화면에서 카드를 등록하면 즉시 활성화됩니다." : "운영자가 결제 연결을 완료한 뒤 구독할 수 있습니다."}</p>
                  {billingActive ? <button className="primary-action" onClick={() => setActiveStep("brand")}>브랜드 설정 시작 →</button> : <button className="primary-action" disabled={!billing.provider_readiness.billing || loadState === "loading"} onClick={() => void startCheckout()}>{loadState === "loading" ? "결제 준비 중…" : "$40 플랜 결제하기"}</button>}
                </footer>
              </div>
            )}
          </>
        )}

        {activeStep === "brand" && (
          <>
            <ScreenHeading number="02" eyebrow="시작점" title="분석할 브랜드를 알려주세요" description="회사와 브랜드를 한 번만 정해 두면 이후 경쟁 광고 수집과 AI 분석의 기준으로 사용합니다." />
            <div className="setup-layout">
              <section className="focus-panel">
                <div className="panel-heading"><div><p className="eyebrow">회사 / 팀</p><h3>작업 공간 선택</h3></div><button className="text-action" onClick={() => setOpenForm(openForm === "org" ? null : "org")}>+ 새 회사/팀</button></div>
                {openForm === "org" && <InlineForm onSubmit={createOrganization} fields={[{ name: "name", placeholder: "회사 또는 팀 이름" }]} />}
                <select className="large-select" aria-label="작업할 회사 또는 팀 선택" value={organizationId} onChange={(event) => void loadOrganization(subject, event.target.value)}>
                  <option value="">작업할 회사/팀을 선택하세요</option>
                  {organizations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
                {organizations.length === 0 && <Empty compact text="저장된 회사가 없습니다. 새 회사/팀을 먼저 만들어 주세요." />}
              </section>

              <section className="focus-panel">
                <div className="panel-heading"><div><p className="eyebrow">브랜드</p><h3>분석 기준 선택</h3></div><button className="text-action" disabled={!organizationId} onClick={() => setOpenForm(openForm === "brand" ? null : "brand")}>+ 새 브랜드</button></div>
                {openForm === "brand" && <InlineForm onSubmit={createBrand} fields={[{ name: "name", placeholder: "브랜드 이름" }, { name: "industry", placeholder: "업종 (예: 뷰티)" }]} />}
                <div className="choice-list">
                  {brands.map((brand) => <button key={brand.id} className={brand.id === brandId ? "selected" : ""} onClick={() => void loadBrand(subject, brand.id, tenantVersion.current)}><span>{brand.name.slice(0, 1).toUpperCase()}</span><div><strong>{brand.name}</strong><small>{brand.industry || "업종 미입력"}</small></div><i>{brand.id === brandId ? "선택됨" : "선택"}</i></button>)}
                </div>
                {organizationId && loadState !== "loading" && brands.length === 0 && <Empty compact text="아직 브랜드가 없습니다. 분석할 브랜드를 추가하세요." />}
              </section>
            </div>
            <StepActions nextLabel="경쟁 시장 설정하기" nextDisabled={!brandId} onNext={() => setActiveStep("market")} />
          </>
        )}

        {activeStep === "market" && (
          <>
            <ScreenHeading number="03" eyebrow={activeBrand?.name || "브랜드"} title="비교할 시장을 좁혀주세요" description="베트남에서 함께 살펴볼 경쟁 브랜드를 등록하세요. 업종 키워드 수집은 다음 단계에서 추가할 수 있습니다." />
            <section className="focus-panel narrow-panel">
              <div className="panel-heading"><div><p className="eyebrow">경쟁 브랜드</p><h3>{competitors.length ? `${competitors.length}개 브랜드를 비교 중` : "아직 등록된 경쟁 브랜드가 없습니다"}</h3></div><button className="text-action" onClick={() => setOpenForm(openForm === "competitor" ? null : "competitor")}>+ 경쟁 브랜드</button></div>
              {openForm === "competitor" && <InlineForm onSubmit={createCompetitor} fields={[{ name: "name", placeholder: "경쟁 브랜드 이름" }, { name: "website", placeholder: "웹사이트 주소 (선택)" }]} />}
              {competitors.length === 0 ? <Empty text="경쟁사를 등록하면 다음 단계에서 Meta 광고를 빠르게 찾아보고 TikTok 자동 수집 대상으로 연결할 수 있습니다. 업종만으로 시작해도 됩니다." /> : <div className="market-list">{competitors.map((item, index) => <div key={item.id}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{item.name}</strong><small>{item.website || "웹사이트 미입력"}</small></div><i>비교 대상</i></div>)}</div>}
            </section>
            <StepActions previousLabel="브랜드로 돌아가기" onPrevious={() => setActiveStep("brand")} nextLabel="자동 수집 설정하기" onNext={() => setActiveStep("collection")} />
          </>
        )}

        {activeStep === "collection" && (
          <>
            <ScreenHeading number="04" eyebrow="시장 광고 조사" title="Meta와 TikTok 광고를 자동으로 모으세요" description="경쟁 브랜드나 업종 키워드를 한 번 설정하면 베트남 공개 광고를 주기적으로 수집합니다. 공식 라이브러리에서 원본도 확인할 수 있습니다." />
            <div className="collection-workflow">
              <section className="collection-channel" aria-labelledby="meta-channel-title">
                <div className="channel-label"><span>META</span><small>자동 수집</small></div>
                <div className="channel-copy">
                  <p className="eyebrow">Facebook · Instagram 공개 광고</p>
                  <h3 id="meta-channel-title">경쟁사 광고와 문구를 수집합니다</h3>
                  <p>Apify를 통해 베트남의 활성 광고를 수집합니다. 공식 API가 아닌 공개 웹 데이터이므로 결과 누락이나 구조 변경 가능성이 있습니다.</p>
                  {(competitors.length > 0 || activeBrand?.industry) && <div className="meta-quick-links" aria-label="Meta 광고 빠른 검색">
                    {competitors.map((item) => <a key={item.id} href={metaLibraryUrl(item.name)} target="_blank" rel="noreferrer">{item.name} ↗</a>)}
                    {activeBrand?.industry && <a href={metaLibraryUrl(activeBrand.industry)} target="_blank" rel="noreferrer">{activeBrand.industry} 업종 ↗</a>}
                  </div>}
                </div>
                <a className="library-action" href={metaLibraryUrl()} target="_blank" rel="noreferrer">공식 라이브러리 <span>↗</span></a>
              </section>

              <section className="collection-channel" aria-labelledby="tiktok-channel-title">
                <div className="channel-label"><span>TIKTOK</span><small>자동 수집</small></div>
                <div className="channel-copy"><p className="eyebrow">Creative Center · Top Ads</p><h3 id="tiktok-channel-title">성과가 좋은 공개 광고 표본을 수집합니다</h3><p>TikTok Creative Center가 공개한 베트남 인기 광고 표본입니다. 특정 경쟁사의 전체 광고 목록은 아닙니다.</p></div>
                <a className="library-action secondary" href={tiktokLibraryUrl} target="_blank" rel="noreferrer">Creative Center <span>↗</span></a>
              </section>

              <section className="focus-panel collection-source-panel">
              <div className="panel-heading"><div><p className="eyebrow">자동 수집 대상</p><h3>{collectionSources.length ? `${collectionSources.length}개 수집 설정됨` : "첫 수집 대상을 추가해 주세요"}</h3></div><button className="text-action" onClick={() => setOpenForm(openForm === "source" ? null : "source")}>+ 수집 대상</button></div>
              <p className="collection-scope-note">플랫폼, 경쟁 브랜드 또는 업종 키워드, 수집 주기를 설정합니다. 새 광고만 중복 없이 저장하고 분석 단계로 보냅니다.</p>
              {openForm === "source" && <CollectionSourceForm competitors={competitors} onSubmit={createCollectionSource} onCancel={() => setOpenForm(null)} />}
              {collectionSources.length === 0 ? <Empty text="Meta 또는 TikTok에서 찾을 경쟁 브랜드나 베트남 업종 키워드를 설정하세요." /> : <div className="collection-list">{collectionSources.map((source) => <div className={`collection-row ${source.status === "paused" ? "paused" : ""}`} key={source.id}><span className={`source-mark source-${source.platform}`}>{source.platform === "meta_ad_library" ? "M" : "T"}</span><div><strong>{platformLabel[source.platform]}</strong><small>{source.scope === "competitor" ? competitors.find((item) => item.id === source.competitor_id)?.name || "경쟁 브랜드" : source.keywords.join(", ")} · {source.country_code} · {source.sync_interval_hours === 24 ? "매일" : `${source.sync_interval_hours}시간마다`}</small>{source.last_error_code && <small className="source-error">최근 수집 오류 · {source.last_error_code}</small>}</div><span>{source.status === "paused" ? "일시중지" : source.last_sync_at ? `최근 ${date(source.last_sync_at)}` : "첫 수집 대기"}</span><div className="collection-actions"><button disabled={source.status === "paused" || collectionJob?.status === "queued" || collectionJob?.status === "processing"} onClick={() => void syncCollectionSource(source.id)}>지금 수집</button><button className="quiet" onClick={() => void updateCollectionSource(source, source.status === "active" ? "paused" : "active")}>{source.status === "active" ? "중지" : "재개"}</button></div></div>)}</div>}
              {collectionJob && <p className={`collection-status status-${collectionJob.status}`}>{collectionStatusLabel[collectionJob.status]}{collectionJob.status === "completed" ? " · 새 광고 분석이 시작되었습니다." : ""}</p>}
              </section>
            </div>
            <StepActions previousLabel="시장 설정으로" onPrevious={() => setActiveStep("market")} nextLabel="수집 광고 분석하기" onNext={() => setActiveStep("analysis")} />
          </>
        )}

        {activeStep === "analysis" && (
          <>
            <ScreenHeading number="05" eyebrow={activeBrand?.name || "광고 분석"} title="수집된 광고에서 패턴을 찾으세요" description="광고를 선택하면 문구와 AI 분석 결과를 나란히 확인할 수 있습니다." aside={<div className="usage-chip"><span>AI 사용 현황</span><strong>분석 {billing?.allowance.analysis_used ?? usage?.calls ?? 0}회</strong><small>남은 credit ${Number(billing?.allowance.credit_remaining_usd ?? 0).toFixed(2)}</small></div>} />
            <div className="analysis-toolbar"><div className="filters"><select aria-label="광고 출처 필터" value={ownershipFilter} onChange={(event) => { setOwnershipFilter(event.target.value); void refresh(event.target.value, mediaFilter); }}><option value="">모든 광고 출처</option><option value="own">우리 브랜드 광고</option><option value="competitor">경쟁 브랜드 광고</option><option value="market">기타 시장 사례</option></select><select aria-label="광고 형식 필터" value={mediaFilter} onChange={(event) => { setMediaFilter(event.target.value); void refresh(ownershipFilter, event.target.value); }}><option value="">모든 광고 형식</option><option value="image">이미지</option><option value="video">영상</option><option value="carousel">여러 장 이미지</option><option value="text">텍스트</option></select></div><button className="secondary-action" onClick={() => setOpenForm(openForm === "creative" ? null : "creative")}>+ 직접 추가</button></div>
            {openForm === "creative" && <CreativeForm competitors={competitors} onSubmit={createCreative} onCancel={() => setOpenForm(null)} />}
            <div className="analysis-workbench">
              <section className="creative-library">
                <div className="library-meta"><span>수집된 광고</span><strong>{creatives.length}개</strong></div>
                {loadState === "loading" && <LoadingRows />}
                {loadState !== "loading" && creatives.length === 0 && <Empty text={collectionSources.length ? "첫 자동 수집을 실행하면 새 광고가 이곳에 표시됩니다." : "Meta 또는 TikTok 자동 수집을 설정하거나 광고를 직접 추가하세요."} />}
                <div className="creative-list">{creatives.map((item, index) => <button key={item.id} className={creative?.id === item.id ? "creative-row selected" : "creative-row"} onClick={() => void selectCreative(item.id)}><span className={`media-tile media-${item.media_type}`}>{mediaLabel[item.media_type].slice(0, 2)}</span><span className="creative-copy"><strong>{item.title || "제목 없는 광고 소재"}</strong><small>{item.body || item.source_url || "입력한 광고 문구 없음"}</small></span><span className="creative-tags"><i>{ownershipLabel[item.ownership_type]}</i><i>{mediaLabel[item.media_type]}</i></span><span className="creative-date">{date(item.created_at)}<small>#{String(index + 1).padStart(2, "0")}</small></span></button>)}</div>
              </section>
              <aside className="inspector-pane">
                {!creative ? <div className="inspector-empty"><span>↗</span><h3>광고를 선택하세요</h3><p>왼쪽 목록에서 소재를 고르면 광고 문구와 분석 결과가 표시됩니다.</p></div> : <div className="inspector-content" key={creative.id}><header className="inspector-header"><p className="eyebrow">선택한 광고</p><span>{mediaLabel[creative.media_type]}</span></header><h3>{creative.title || "제목 없는 광고 소재"}</h3><p className="creative-body">{creative.body || "입력한 광고 문구가 없습니다."}</p>{creative.source_url && <a className="source-link" href={creative.source_url} target="_blank" rel="noreferrer">원본 광고 보기 ↗</a>}<dl className="detail-grid"><div><dt>광고 출처</dt><dd>{ownershipLabel[creative.ownership_type]}</dd></div><div><dt>등록일</dt><dd>{date(creative.created_at)}</dd></div></dl><div className="analysis-heading"><div><p className="eyebrow">AI 광고 분석</p><h4>{analysis ? "분석 결과" : "아직 분석하지 않음"}</h4></div><button className="analyze-button" disabled={isAnalyzing} onClick={() => void analyze()}>{isAnalyzing ? "분석 중…" : analysis ? "다시 분석" : "AI로 분석"}</button></div>{job && <div className={`job-status status-${job.status}`}><div><span /><strong>{jobStatusLabel[job.status]}</strong><small>처리 시도 {job.attempts}회</small></div><progress max="100" value={job.progress} aria-label="분석 진행률" />{job.error_message && <p>{job.error_message}</p>}</div>}{!analysis && !isAnalyzing && <Empty compact text="AI가 첫 문구, 혜택, 유도 행동과 설득 관점을 정리해 드립니다." />}{analysis && <div className="analysis-result"><p className="analysis-summary">{analysis.summary}</p><AnalysisLine label="첫 문구" value={analysis.hook} /><AnalysisLine label="혜택·제안" value={analysis.offer} /><AnalysisLine label="유도 행동" value={analysis.cta} /><AnalysisLine label="설득 관점" value={analysis.angle} /><div className="tag-cloud">{analysis.tags.map((tag) => <span key={tag}>#{tag}</span>)}</div><div className="confidence"><span>분석 신뢰도</span><strong>{Math.round(analysis.confidence * 100)}%</strong></div><details className="model-note"><summary>분석 세부 정보</summary>{analysis.provider} · {analysis.model} · {analysis.prompt_version}</details></div>}</div>}
              </aside>
            </div>
            <StepActions previousLabel="자동 수집으로" onPrevious={() => setActiveStep("collection")} />
          </>
        )}
      </section>
    </main>
  );
}

function ScreenHeading({ number, eyebrow, title, description, aside }: { number: string; eyebrow: string; title: string; description: string; aside?: ReactNode }) {
  return <header className="screen-heading"><span>{number}</span><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>{aside}</header>;
}

function StepActions({ previousLabel, onPrevious, nextLabel, onNext, nextDisabled = false }: { previousLabel?: string; onPrevious?: () => void; nextLabel?: string; onNext?: () => void; nextDisabled?: boolean }) {
  return <footer className="step-actions"><div>{previousLabel && <button className="back-action" onClick={onPrevious}>← {previousLabel}</button>}</div>{nextLabel && <button className="primary-action" disabled={nextDisabled} onClick={onNext}>{nextLabel} →</button>}</footer>;
}

function InlineForm({ onSubmit, fields }: { onSubmit: (event: FormEvent<HTMLFormElement>) => void; fields: { name: string; placeholder: string }[] }) {
  return <form className="inline-form" onSubmit={onSubmit}>{fields.map((field) => <input key={field.name} name={field.name} placeholder={field.placeholder} required={field.name === "name"} />)}<button>저장</button></form>;
}

function CreativeForm({ competitors, onSubmit, onCancel }: { competitors: Competitor[]; onSubmit: (event: FormEvent<HTMLFormElement>) => void; onCancel: () => void }) {
  const [ownership, setOwnership] = useState("own");
  return <form className="creative-form" onSubmit={onSubmit}><div className="form-heading"><div><p className="eyebrow">새 광고 소재</p><h3>분석할 광고 등록</h3></div><button type="button" onClick={onCancel}>닫기</button></div><p className="form-description">광고에서 보이는 문구를 입력하면 AI가 메시지와 설득 방식을 분석합니다.</p><div className="form-grid"><label>이 광고의 출처<select name="ownership_type" value={ownership} onChange={(event) => setOwnership(event.target.value)}><option value="own">우리 브랜드 광고</option><option value="competitor">경쟁 브랜드 광고</option><option value="market">기타 시장 사례</option></select></label><label>광고 형식<select name="media_type"><option value="image">이미지</option><option value="video">영상</option><option value="carousel">여러 장 이미지</option><option value="text">텍스트</option></select></label>{ownership === "competitor" && <label>어느 경쟁 브랜드인가요?<select name="competitor_id" required><option value="">경쟁 브랜드 선택</option>{competitors.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>}<label className="wide">소재 이름<input name="title" placeholder="예: 여름 수분크림 할인 광고" /></label><label className="wide">광고에 나온 문구<textarea name="body" rows={3} placeholder="제목, 본문, 버튼 문구 등 분석할 내용을 붙여 넣으세요." /></label><label className="wide">원본 광고 주소<input name="source_url" type="url" placeholder="https:// (선택 사항)" /></label></div><button className="primary-action">광고 소재 저장</button></form>;
}

function CollectionSourceForm({ competitors, onSubmit, onCancel }: { competitors: Competitor[]; onSubmit: (event: FormEvent<HTMLFormElement>) => void; onCancel: () => void }) {
  const [scope, setScope] = useState(competitors.length ? "competitor" : "industry");
  const [platform, setPlatform] = useState("meta_ad_library");
  return <form className="creative-form source-form" onSubmit={onSubmit}><div className="form-heading"><div><p className="eyebrow">새 자동 수집 대상</p><h3>어떤 광고를 자동으로 찾아볼까요?</h3></div><button type="button" onClick={onCancel}>닫기</button></div><div className="form-grid"><label>광고 플랫폼<select name="platform" value={platform} onChange={(event) => setPlatform(event.target.value)}><option value="meta_ad_library">Meta 광고 라이브러리</option><option value="tiktok_creative_center">TikTok Creative Center</option></select></label><label>찾는 기준<select name="scope" value={scope} onChange={(event) => setScope(event.target.value)}><option value="competitor">경쟁 브랜드</option><option value="industry">업종·키워드</option></select></label>{scope === "competitor" ? <label className="wide">경쟁 브랜드<select name="competitor_id" required><option value="">선택하세요</option>{competitors.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label> : <label className="wide">검색어<input name="keywords" required placeholder="예: 스킨케어, 선크림, kem chống nắng" /></label>}<label>대상 국가<input name="country_code" defaultValue="VN" maxLength={2} required /></label><label>광고 언어<input name="language_code" defaultValue="vi" /></label><label>자동 수집 주기<select name="sync_interval_hours" defaultValue="24"><option value="6">6시간마다</option><option value="12">12시간마다</option><option value="24">매일</option><option value="72">3일마다</option><option value="168">매주</option></select></label><label className="wide">{platform === "meta_ad_library" ? "Facebook 페이지 또는 광고 라이브러리 주소" : "TikTok 계정명 또는 식별자"}<input name="external_identifier" placeholder={platform === "meta_ad_library" ? "https://www.facebook.com/brand (선택 사항)" : "예: @competitor (선택 사항)"} /></label></div><button className="primary-action">자동 수집 대상 저장</button></form>;
}

function ProviderState({ label, ready }: { label: string; ready: boolean }) { return <div className={ready ? "ready" : "waiting"}><span>{label}</span><strong>{ready ? "연결됨" : "운영 설정 전"}</strong></div>; }
function Empty({ text, compact = false }: { text: string; compact?: boolean }) { return <div className={compact ? "empty-state compact" : "empty-state"}><span>○</span><p>{text}</p></div>; }
function LoadingRows() { return <div className="loading-rows" aria-label="광고 소재 불러오는 중">{[1, 2, 3].map((item) => <div key={item}><span /><i /></div>)}</div>; }
function AnalysisLine({ label, value }: { label: string; value: string | null }) { return <div className="analysis-line"><span>{label}</span><p>{value || "분석 결과 없음"}</p></div>; }
