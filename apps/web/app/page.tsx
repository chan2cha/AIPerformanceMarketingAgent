import { MarketingWorkspace } from "./workspace";

type Health = { status: "ok" };

async function getApiHealth(): Promise<boolean> {
  const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}/health`, { cache: "no-store" });
    if (!response.ok) return false;
    return ((await response.json()) as Health).status === "ok";
  } catch {
    return false;
  }
}

export default async function Home() {
  return <MarketingWorkspace initialApiHealthy={await getApiHealth()} />;
}
