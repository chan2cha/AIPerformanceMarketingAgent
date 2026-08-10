type Health = {
  status: "ok";
};

async function getApiHealth(): Promise<Health | null> {
  const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${apiUrl}/health`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as Health;
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getApiHealth();
  const isHealthy = health?.status === "ok";

  return (
    <main>
      <section>
        <p className="eyebrow">Repository Bootstrap · Phase 0</p>
        <h1>AI Performance Marketing</h1>
        <p className="description">
          경쟁사 광고 관찰부터 성과 학습과 다음 가설 추천까지 연결하는 B2B SaaS입니다.
        </p>
        <div className="health" aria-live="polite">
          <span className={isHealthy ? "dot healthy" : "dot unhealthy"} aria-hidden="true" />
          API 상태: {isHealthy ? "정상" : "연결 안 됨"}
        </div>
      </section>
    </main>
  );
}
