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

COUNTRY_MAP = {
    "any": "",
    "russia": "0",
    "ukraine": "1",
    "china": "3",
    "philippines": "4",
    "indonesia": "6",
    "uk": "16",
    "england": "16",
    "india": "22",
    "germany": "43",
    "netherlands": "48",
    "poland": "15",
    "turkey": "62",
    "brazil": "73",
    "france": "78",
    "canada": "36",
    "usa": "187",
    "spain": "56",
    "italy": "86",
    "mexico": "54",
    "egypt": "21",
    "nigeria": "19",
    "kenya": "63",
    "southafrica": "31",
    "argentina": "39",
    "colombia": "33",
    "thailand": "52",
    "vietnam": "10",
    "malaysia": "7",
    "pakistan": "14",
    "bangladesh": "60",
    "japan": "182",
    "southkorea": "190",
    "australia": "175",
    "sweden": "46",
    "portugal": "117",
    "romania": "32",
    "czech": "63",
    "morocco": "37",
}

SERVICE_MAP = {
    "whatsapp": "wa",
    "telegram": "tg",
    "facebook": "fb",
    "instagram": "ig",
    "google": "go",
    "twitter": "tw",
    "tiktok": "lf",
    "uber": "ub",
    "amazon": "am",
    "microsoft": "ms",
    "yahoo": "mb",
    "linkedin": "oi",
    "discord": "ds",
    "snapchat": "fu",
    "viber": "vi",
    "wechat": "wx",
    "line": "me",
    "signal": "sy",
    "netflix": "nf",
    "spotify": "sf",
    "paypal": "pp",
    "steam": "mt",
    "apple": "wx",
    "airbnb": "ab",
    "aliexpress": "hw",
    "openai": "dr",
    "chatgpt": "dr",
}

_REVERSE_SERVICE_MAP = {v: k for k, v in SERVICE_MAP.items()}


class SMSActivateProvider(SMSProvider):
    name = "sms-activate"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = httpx.Client(timeout=30.0)
        self._base = "https://api.sms-activate.org/stubs/handler_api.php"

    def _request(self, **params) -> str:
        params["api_key"] = self._api_key
        resp = self._client.get(self._base, params=params)
        resp.raise_for_status()
        text = resp.text.strip()
        self._check_errors(text)
        return text

    def get_balance(self) -> Balance:
        result = self._request(action="getBalance")
        amount = 0.0
        if ":" in result:
            try:
                amount = float(result.split(":")[1])
            except (ValueError, IndexError):
                pass
        return Balance(amount=amount, currency="RUB", provider=self.name)

    def get_services(self, country: str = "any") -> list[ServiceInfo]:
        params = {"action": "getPrices", "api_key": self._api_key}
        country_code = self._resolve_country(country)
        if country_code:
            params["country"] = country_code

        resp = self._client.get(self._base, params=params)
        resp.raise_for_status()

        try:
            data = resp.json()
        except Exception:
            return []

        results = []
        for cid, services in data.items():
            if not isinstance(services, dict):
                continue
            for svc_code, info in services.items():
                if not isinstance(info, dict):
                    continue
                display_name = _REVERSE_SERVICE_MAP.get(svc_code, svc_code)
                count = int(info.get("count", 0))
                cost = float(info.get("cost", 0))
                if count > 0:
                    results.append(
                        ServiceInfo(
                            name=display_name,
                            quantity=count,
                            price=cost,
                            country=country,
                        )
                    )

        seen = {}
        for svc in results:
            key = svc.name
            if key not in seen or svc.quantity > seen[key].quantity:
                seen[key] = svc
        return sorted(seen.values(), key=lambda s: s.name)

    def buy_number(
        self, service: str, country: str = "any", operator: str = "any"
    ) -> Order:
        svc_code = SERVICE_MAP.get(service.lower(), service)
        country_code = self._resolve_country(country)

        params: dict = {"action": "getNumber", "service": svc_code}
        if country_code:
            params["country"] = country_code
        if operator != "any":
            params["operator"] = operator

        result = self._request(**params)
        parts = result.split(":")

        if len(parts) < 3 or parts[0] != "ACCESS_NUMBER":
            raise ProviderError(f"Unexpected response: {result}")

        return Order(
            id=int(parts[1]),
            phone=parts[2],
            country=country,
            service=service,
            price=0,
            status=OrderStatus.PENDING,
            provider=self.name,
        )

    def check_order(self, order_id: int) -> Order:
        result = self._request(action="getStatus", id=str(order_id))

        sms_code = None
        status = OrderStatus.PENDING

        if result == "STATUS_WAIT_CODE":
            status = OrderStatus.PENDING
        elif result.startswith("STATUS_WAIT_RETRY"):
            status = OrderStatus.PENDING
            if ":" in result:
                sms_code = result.split(":", 1)[1]
        elif result.startswith("STATUS_OK"):
            status = OrderStatus.RECEIVED
            if ":" in result:
                sms_code = result.split(":", 1)[1]
        elif result == "STATUS_CANCEL":
            status = OrderStatus.CANCELED

        return Order(
            id=order_id,
            phone="",
            country="",
            service="",
            price=0,
            status=status,
            sms_code=sms_code,
            sms_text=sms_code,
            provider=self.name,
        )

    def cancel_order(self, order_id: int) -> bool:
        result = self._request(action="setStatus", id=str(order_id), status="8")
        return "ACCESS_CANCEL" in result

    def finish_order(self, order_id: int) -> bool:
        result = self._request(action="setStatus", id=str(order_id), status="6")
        return "ACCESS_ACTIVATION" in result

    def _resolve_country(self, country: str) -> str:
        if country == "any":
            return ""
        mapped = COUNTRY_MAP.get(country.lower())
        if mapped is not None:
            return mapped
        if country.isdigit():
            return country
        return country

    def _check_errors(self, text: str):
        error_map = {
            "BAD_KEY": AuthenticationError("Invalid SMS-Activate API key"),
            "ERROR_SQL": ProviderError("Provider internal error"),
            "NO_NUMBERS": NoNumbersAvailable("No numbers available"),
            "NO_BALANCE": InsufficientBalance("Insufficient account balance"),
            "WRONG_SERVICE": ProviderError("Invalid service code"),
            "NO_ACTIVATION": OrderNotFound("Order not found"),
            "BAD_STATUS": ProviderError("Invalid status transition"),
        }
        for key, exc in error_map.items():
            if text == key or text.startswith(key):
                raise exc
