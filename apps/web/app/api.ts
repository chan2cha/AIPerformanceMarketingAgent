const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ErrorPayload = { error?: { message?: string } };

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

export async function apiRequest<T>(
  path: string,
  subject: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer dev:${subject}`);
  if (init.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
  if (!response.ok) {
    let payload: ErrorPayload = {};
    try {
      payload = (await response.json()) as ErrorPayload;
    } catch {
      // A generic message is safer than leaking an upstream response body.
    }
    throw new ApiError(payload.error?.message ?? "요청을 처리하지 못했습니다.", response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
