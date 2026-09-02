import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import parse_qs

import httpx

from app.core.errors import AppError, ServiceUnavailableError


@dataclass(frozen=True)
class CheckoutSession:
    url: str


class BillingProvider(Protocol):
    def create_checkout(self, organization_id: str, organization_name: str) -> CheckoutSession: ...

    def create_portal(self, customer_id: str) -> str: ...


class StripeBillingProvider:
    def __init__(
        self,
        *,
        secret_key: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        api_base_url: str = "https://api.stripe.com/v1",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._secret_key = secret_key
        self._price_id = price_id
        self._success_url = success_url
        self._cancel_url = cancel_url
        self._api_base_url = api_base_url.rstrip("/")
        self._http_client = http_client

    def _post(self, path: str, data: dict[str, str]) -> dict[str, Any]:
        client = self._http_client or httpx.Client(timeout=30)
        owns_client = self._http_client is None
        try:
            response = client.post(
                f"{self._api_base_url}{path}",
                data=data,
                headers={"Authorization": f"Bearer {self._secret_key}"},
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise ServiceUnavailableError(
                code="BILLING_PROVIDER_UNAVAILABLE",
                message="결제 서비스를 일시적으로 사용할 수 없습니다.",
            ) from error
        finally:
            if owns_client:
                client.close()
        if response.status_code >= 400:
            raise ServiceUnavailableError(
                code="BILLING_PROVIDER_ERROR",
                message="결제 요청을 시작하지 못했습니다.",
            )
        return dict(response.json())

    def create_checkout(self, organization_id: str, organization_name: str) -> CheckoutSession:
        payload = self._post(
            "/checkout/sessions",
            {
                "mode": "subscription",
                "line_items[0][price]": self._price_id,
                "line_items[0][quantity]": "1",
                "success_url": self._success_url,
                "cancel_url": self._cancel_url,
                "client_reference_id": organization_id,
                "metadata[organization_id]": organization_id,
                "metadata[organization_name]": organization_name,
                "subscription_data[metadata][organization_id]": organization_id,
                "allow_promotion_codes": "true",
            },
        )
        url = payload.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ServiceUnavailableError(
                code="BILLING_PROVIDER_INVALID_RESPONSE",
                message="결제 서비스 응답이 올바르지 않습니다.",
            )
        return CheckoutSession(url=url)

    def create_portal(self, customer_id: str) -> str:
        payload = self._post(
            "/billing_portal/sessions",
            {"customer": customer_id, "return_url": self._success_url},
        )
        url = payload.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ServiceUnavailableError(
                code="BILLING_PROVIDER_INVALID_RESPONSE",
                message="결제 관리 화면을 열지 못했습니다.",
            )
        return url


def verify_stripe_webhook(
    payload: bytes,
    signature_header: str,
    webhook_secret: str,
    *,
    tolerance_seconds: int = 300,
    now: int | None = None,
) -> dict[str, Any]:
    values = parse_qs(signature_header.replace(",", "&"))
    timestamp_values = values.get("t")
    signature_values = values.get("v1")
    if not timestamp_values or not signature_values:
        raise AppError(400, "INVALID_WEBHOOK_SIGNATURE", "결제 webhook 서명이 없습니다.")
    try:
        timestamp = int(timestamp_values[0])
    except ValueError as error:
        raise AppError(
            400, "INVALID_WEBHOOK_SIGNATURE", "결제 webhook 서명이 잘못되었습니다."
        ) from error
    current_time = int(time.time()) if now is None else now
    if abs(current_time - timestamp) > tolerance_seconds:
        raise AppError(400, "EXPIRED_WEBHOOK_SIGNATURE", "결제 webhook 서명이 만료되었습니다.")
    signed_payload = f"{timestamp}.".encode() + payload
    expected = hmac.new(webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, signature) for signature in signature_values):
        raise AppError(400, "INVALID_WEBHOOK_SIGNATURE", "결제 webhook 서명이 잘못되었습니다.")
    try:
        event = json.loads(payload)
    except json.JSONDecodeError as error:
        raise AppError(
            400, "INVALID_WEBHOOK_PAYLOAD", "결제 webhook 본문이 잘못되었습니다."
        ) from error
    if not isinstance(event, dict):
        raise AppError(400, "INVALID_WEBHOOK_PAYLOAD", "결제 webhook 본문이 잘못되었습니다.")
    return event
