from httpx import ASGITransport, AsyncClient, Response

from app.main import app


def auth_headers(subject: str) -> dict[str, str]:
    return {"Authorization": f"Bearer dev:{subject}"}


class ApiClient:
    def __init__(self) -> None:
        self._client = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        )

    async def __aenter__(self) -> "ApiClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.__aexit__(*args)

    async def get(self, url: str, subject: str | None = None) -> Response:
        headers = auth_headers(subject) if subject else None
        return await self._client.get(url, headers=headers)

    async def post(
        self,
        url: str,
        subject: str,
        payload: dict[str, object],
        extra_headers: dict[str, str] | None = None,
    ) -> Response:
        headers = auth_headers(subject)
        headers.update(extra_headers or {})
        return await self._client.post(url, headers=headers, json=payload)

    async def patch(self, url: str, subject: str, payload: dict[str, object]) -> Response:
        return await self._client.patch(url, headers=auth_headers(subject), json=payload)

    async def delete(self, url: str, subject: str) -> Response:
        return await self._client.delete(url, headers=auth_headers(subject))
