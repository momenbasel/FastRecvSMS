import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

CONFIG_DIR = Path.home() / ".config" / "fastrecvsms"
CONFIG_FILE = CONFIG_DIR / "config.toml"

_DEFAULT_CONFIG = {
    "default_provider": "5sim",
    "default_country": "any",
    "providers": {
        "5sim": {"api_key": ""},
        "sms-activate": {"api_key": ""},
    },
    "display": {
        "poll_interval": 5,
        "max_wait_time": 600,
    },
}


class Config:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "rb") as f:
                data = tomllib.load(f)
            merged = _DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
        return _deep_copy(_DEFAULT_CONFIG)

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "wb") as f:
            tomli_w.dump(self._data, f)

    def get_api_key(self, provider: str) -> str:
        env_map = {
            "5sim": "FASTRECVSMS_5SIM_API_KEY",
            "sms-activate": "FASTRECVSMS_SMS_ACTIVATE_API_KEY",
        }
        env_key = env_map.get(provider, f"FASTRECVSMS_{provider.upper().replace('-', '_')}_API_KEY")
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val
        return self._data.get("providers", {}).get(provider, {}).get("api_key", "")

    def set_api_key(self, provider: str, key: str):
        if "providers" not in self._data:
            self._data["providers"] = {}
        if provider not in self._data["providers"]:
            self._data["providers"][provider] = {}
        self._data["providers"][provider]["api_key"] = key
        self.save()

    @property
    def default_provider(self) -> str:
        return self._data.get("default_provider", "5sim")

    @default_provider.setter
    def default_provider(self, value: str):
        self._data["default_provider"] = value
        self.save()

    @property
    def default_country(self) -> str:
        return self._data.get("default_country", "any")

    @property
    def poll_interval(self) -> int:
        return self._data.get("display", {}).get("poll_interval", 5)

    @property
    def max_wait_time(self) -> int:
        return self._data.get("display", {}).get("max_wait_time", 600)

    @property
    def data(self) -> dict:
        return self._data


def _deep_copy(d: dict) -> dict:
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _deep_copy(v)
        else:
            result[k] = v
    return result
