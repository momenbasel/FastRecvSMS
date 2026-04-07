import httpx

from fastrecvsms.exceptions import (
    AuthenticationError,
    InsufficientBalance,
    NoNumbersAvailable,
    OrderNotFound,
    ProviderError,
)
from fastrecvsms.models import Balance, Order, OrderStatus, ServiceInfo
from fastrecvsms.providers.base import SMSProvider

_STATUS_MAP = {
    "PENDING": OrderStatus.PENDING,
    "RECEIVED": OrderStatus.RECEIVED,
    "CANCELED": OrderStatus.CANCELED,
    "TIMEOUT": OrderStatus.TIMEOUT,
    "FINISHED": OrderStatus.FINISHED,
    "BANNED": OrderStatus.BANNED,
}


class FiveSimProvider(SMSProvider):
    name = "5sim"

    def __init__(self, api_key: str):
        self._client = httpx.Client(
            base_url="https://5sim.net/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def get_balance(self) -> Balance:
        resp = self._client.get("/user/profile")
        self._check_auth(resp)
        resp.raise_for_status()
        data = resp.json()
        return Balance(
            amount=data.get("balance", 0),
            currency="RUB",
            provider=self.name,
        )

    def get_services(self, country: str = "any") -> list[ServiceInfo]:
        resp = self._client.get(f"/guest/products/{country}/any")
        resp.raise_for_status()
        data = resp.json()
        results = []
        for svc_name, svc_data in data.items():
            if not isinstance(svc_data, dict):
                continue
            qty = svc_data.get("Qty", svc_data.get("qty", 0))
            price = svc_data.get("Price", svc_data.get("price", 0))
            if qty > 0:
                results.append(
                    ServiceInfo(
                        name=svc_name,
                        quantity=int(qty),
                        price=float(price),
                        country=country,
                    )
                )
        return sorted(results, key=lambda s: s.name)

    def buy_number(
        self, service: str, country: str = "any", operator: str = "any"
    ) -> Order:
        resp = self._client.get(
            f"/user/buy/activation/{country}/{operator}/{service}"
        )
        self._check_auth(resp)

        text = resp.text.strip()
        if resp.status_code == 200 and not text.startswith("{"):
            if "no free phones" in text.lower():
                raise NoNumbersAvailable(
                    f"No numbers available for {service} in {country}"
                )
            if "not enough" in text.lower() or "balance" in text.lower():
                raise InsufficientBalance("Insufficient account balance")
            raise ProviderError(f"Unexpected response: {text}")

        if resp.status_code != 200:
            raise ProviderError(f"HTTP {resp.status_code}: {text}")

        data = resp.json()
        return Order(
            id=data["id"],
            phone=data.get("phone", ""),
            country=data.get("country", country),
            service=service,
            price=float(data.get("price", 0)),
            status=OrderStatus.PENDING,
            provider=self.name,
            created_at=data.get("created_at"),
        )

    def check_order(self, order_id: int) -> Order:
        resp = self._client.get(f"/user/check/{order_id}")
        self._check_auth(resp)

        if resp.status_code == 404:
            raise OrderNotFound(f"Order {order_id} not found")

        resp.raise_for_status()
        data = resp.json()

        sms_code = None
        sms_text = None
        sms_data = data.get("sms")
        if isinstance(sms_data, list) and len(sms_data) > 0:
            sms_code = sms_data[0].get("code", "")
            sms_text = sms_data[0].get("text", "")
        elif isinstance(sms_data, dict):
            sms_code = sms_data.get("code", "")
            sms_text = sms_data.get("text", "")

        raw_status = data.get("status", "PENDING")
        status = _STATUS_MAP.get(raw_status, OrderStatus.PENDING)

        return Order(
            id=data.get("id", order_id),
            phone=data.get("phone", ""),
            country=data.get("country", ""),
            service=data.get("product", ""),
            price=float(data.get("price", 0)),
            status=status,
            sms_code=sms_code,
            sms_text=sms_text,
            provider=self.name,
            created_at=data.get("created_at"),
        )

    def cancel_order(self, order_id: int) -> bool:
        resp = self._client.get(f"/user/cancel/{order_id}")
        self._check_auth(resp)
        return resp.status_code == 200

    def finish_order(self, order_id: int) -> bool:
        resp = self._client.get(f"/user/finish/{order_id}")
        self._check_auth(resp)
        return resp.status_code == 200

    def _check_auth(self, resp: httpx.Response):
        if resp.status_code == 401:
            raise AuthenticationError("Invalid 5sim API key")
