from fastrecvsms.providers.base import SMSProvider
from fastrecvsms.providers.fivesim import FiveSimProvider
from fastrecvsms.providers.smsactivate import SMSActivateProvider

PROVIDERS: dict[str, type[SMSProvider]] = {
    "5sim": FiveSimProvider,
    "sms-activate": SMSActivateProvider,
}


def get_provider(name: str, api_key: str) -> SMSProvider:
    provider_class = PROVIDERS.get(name)
    if not provider_class:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider: {name}. Available: {available}")
    return provider_class(api_key)
