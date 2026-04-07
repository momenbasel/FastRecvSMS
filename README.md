# FastRecvSMS

Enterprise SMS verification toolkit for security professionals. Purchase temporary phone numbers and receive SMS verification codes through a unified CLI with multi-provider support.

[![PyPI](https://img.shields.io/pypi/v/fastrecvsms)](https://pypi.org/project/fastrecvsms/)
[![Python](https://img.shields.io/pypi/pyversions/fastrecvsms)](https://pypi.org/project/fastrecvsms/)
[![License](https://img.shields.io/github/license/momenbasel/FastRecvSMS)](LICENSE)

---

## Features

- **Multi-Provider** - Unified interface for 5sim.net and SMS-Activate
- **Real-Time Monitoring** - Live terminal display with animated status while waiting for SMS
- **Auto-Wait** - Buy a number and automatically wait for the verification code in one command
- **Secure Config** - API keys stored locally in TOML config, with environment variable overrides
- **Rich Terminal UI** - Color-coded status, formatted tables, and clear verification code display
- **Graceful Interrupts** - Ctrl+C during wait offers to cancel or preserve the order

## Installation

### From Source

```bash
git clone https://github.com/momenbasel/FastRecvSMS.git
cd FastRecvSMS
pip install -e .
```

### From PyPI

```bash
pip install fastrecvsms
```

## Quick Start

**1. Configure a provider**

```bash
fastrecvsms config set-key 5sim YOUR_API_KEY
```

Get your key from [5sim.net/settings/security](https://5sim.net/settings/security) or [sms-activate.org](https://sms-activate.org/en/api2).

**2. Buy a number and receive SMS**

```bash
fastrecvsms buy whatsapp --country russia
```

The tool purchases a number, then waits in real-time until the verification code arrives.

## Commands

### Account

```bash
fastrecvsms balance                          # Check account balance
fastrecvsms balance -p sms-activate          # Balance for specific provider
```

### Services

```bash
fastrecvsms services                         # List all available services
fastrecvsms services russia                  # Services in a specific country
fastrecvsms services --search whats          # Search by name
fastrecvsms services usa -p sms-activate     # Specific provider + country
```

### Buy & Receive

```bash
fastrecvsms buy telegram                     # Buy + auto-wait for SMS
fastrecvsms buy instagram --country usa      # Specify country
fastrecvsms buy facebook --no-wait           # Purchase only, check later
fastrecvsms buy google --timeout 300         # Custom timeout (seconds)
```

### Order Management

```bash
fastrecvsms check 387141506                  # Check order status
fastrecvsms check 387141506 --wait           # Wait for SMS on existing order
fastrecvsms cancel 387141506                 # Cancel an order
fastrecvsms cancel 387141506 -y              # Cancel without confirmation
fastrecvsms finish 387141506                 # Mark order complete
```

### Configuration

```bash
fastrecvsms config set-key 5sim KEY          # Save API key
fastrecvsms config set-key sms-activate KEY  # Save API key
fastrecvsms config set-default sms-activate  # Switch default provider
fastrecvsms config show                      # View current settings
fastrecvsms config path                      # Config file location
```

## Configuration

Configuration is stored at `~/.config/fastrecvsms/config.toml`:

```toml
default_provider = "5sim"
default_country = "any"

[providers.5sim]
api_key = "your-5sim-key"

[providers.sms-activate]
api_key = "your-sms-activate-key"

[display]
poll_interval = 5
max_wait_time = 600
```

### Environment Variables

Override config values with environment variables:

| Variable | Description |
|---|---|
| `FASTRECVSMS_5SIM_API_KEY` | 5sim.net API key |
| `FASTRECVSMS_SMS_ACTIVATE_API_KEY` | SMS-Activate API key |

Environment variables take precedence over the config file.

## Supported Providers

| Provider | Website | Notes |
|---|---|---|
| **5sim** | [5sim.net](https://5sim.net) | Default. Fast activations, competitive pricing. |
| **SMS-Activate** | [sms-activate.org](https://sms-activate.org) | 600+ services, 180+ countries, large inventory. |

### SMS-Activate Country Names

SMS-Activate uses numeric country codes internally. FastRecvSMS maps common names automatically:

```
russia, usa, uk, germany, france, india, brazil, turkey,
netherlands, indonesia, philippines, china, canada, spain,
italy, mexico, egypt, nigeria, kenya, australia, japan, ...
```

Pass a numeric code directly if your country isn't mapped: `--country 187`

## CLI Aliases

Both `fastrecvsms` and `frsms` are registered as entry points:

```bash
frsms buy telegram --country russia
```

## Programmatic Usage

Import the package directly for scripting:

```python
from fastrecvsms.config import Config
from fastrecvsms.providers import get_provider

config = Config()
provider = get_provider("5sim", config.get_api_key("5sim"))

order = provider.buy_number("whatsapp", "russia")
print(f"Phone: {order.phone}")

result = provider.check_order(order.id)
if result.sms_code:
    print(f"Code: {result.sms_code}")
```

## Requirements

- Python 3.9+
- Dependencies: typer, rich, httpx, pydantic, tomli-w

## License

MIT License - see [LICENSE](LICENSE) for details.
