import time
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live

from fastrecvsms import __version__
from fastrecvsms.config import Config
from fastrecvsms.display import (
    render_balance_panel,
    render_config_panel,
    render_order_panel,
    render_services_table,
    show_error,
    show_success,
)
from fastrecvsms.exceptions import FastRecvSMSError
from fastrecvsms.models import OrderStatus
from fastrecvsms.providers import PROVIDERS, get_provider

console = Console()

app = typer.Typer(
    name="fastrecvsms",
    help="Enterprise SMS verification toolkit for security professionals.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
)

config_app = typer.Typer(
    name="config",
    help="Manage configuration and API keys.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


def _resolve_provider(provider_name: Optional[str] = None):
    cfg = Config()
    name = provider_name or cfg.default_provider
    api_key = cfg.get_api_key(name)
    if not api_key:
        show_error(
            f"No API key configured for [bold]{name}[/bold]\n"
            f"  Run: [cyan]fastrecvsms config set-key {name} YOUR_API_KEY[/cyan]"
        )
        raise typer.Exit(1)
    return get_provider(name, api_key)


def _version_callback(value: bool):
    if value:
        console.print(f"FastRecvSMS v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    pass


@app.command()
def balance(
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Provider to query."
    ),
):
    """Check account balance."""
    p = _resolve_provider(provider)
    try:
        bal = p.get_balance()
        console.print(render_balance_panel(bal))
    except FastRecvSMSError as e:
        show_error(str(e))
        raise typer.Exit(1)


@app.command()
def services(
    country: str = typer.Argument("any", help="Country name or code."),
    search: Optional[str] = typer.Option(
        None, "--search", "-s", help="Filter services by name."
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Provider to query."
    ),
):
    """List available services and pricing."""
    p = _resolve_provider(provider)
    try:
        svcs = p.get_services(country)
        if search:
            term = search.lower()
            svcs = [s for s in svcs if term in s.name.lower()]
        console.print(render_services_table(svcs, country))
    except FastRecvSMSError as e:
        show_error(str(e))
        raise typer.Exit(1)


@app.command()
def buy(
    service: str = typer.Argument(help="Service name (whatsapp, telegram, etc)."),
    country: str = typer.Option("any", "--country", "-c", help="Target country."),
    no_wait: bool = typer.Option(
        False, "--no-wait", help="Purchase only, don't wait for SMS."
    ),
    timeout: int = typer.Option(
        600, "--timeout", "-t", help="Max seconds to wait for SMS."
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Provider to use."
    ),
):
    """Buy a temporary number and receive SMS verification code."""
    p = _resolve_provider(provider)
    try:
        order = p.buy_number(service, country)
        console.print(render_order_panel(order))

        if no_wait:
            console.print(
                f"\n[dim]Check later: fastrecvsms check {order.id} --wait[/dim]"
            )
            return

        console.print()
        _wait_for_sms(p, order.id, timeout)

    except FastRecvSMSError as e:
        show_error(str(e))
        raise typer.Exit(1)


@app.command()
def check(
    order_id: int = typer.Argument(help="Order ID to check."),
    wait: bool = typer.Option(
        False, "--wait", "-w", help="Wait for SMS in real-time."
    ),
    timeout: int = typer.Option(
        600, "--timeout", "-t", help="Max seconds to wait."
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Provider to query."
    ),
):
    """Check order status or wait for incoming SMS."""
    p = _resolve_provider(provider)
    try:
        if wait:
            _wait_for_sms(p, order_id, timeout)
        else:
            order = p.check_order(order_id)
            console.print(render_order_panel(order))
    except FastRecvSMSError as e:
        show_error(str(e))
        raise typer.Exit(1)


@app.command()
def cancel(
    order_id: int = typer.Argument(help="Order ID to cancel."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Provider to use."
    ),
):
    """Cancel an active order."""
    if not yes and not typer.confirm(f"Cancel order {order_id}?"):
        raise typer.Abort()

    p = _resolve_provider(provider)
    try:
        if p.cancel_order(order_id):
            show_success(f"Order {order_id} canceled")
        else:
            show_error(f"Could not cancel order {order_id}")
            raise typer.Exit(1)
    except FastRecvSMSError as e:
        show_error(str(e))
        raise typer.Exit(1)


@app.command()
def finish(
    order_id: int = typer.Argument(help="Order ID to finish."),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Provider to use."
    ),
):
    """Mark an order as completed."""
    p = _resolve_provider(provider)
    try:
        if p.finish_order(order_id):
            show_success(f"Order {order_id} finished")
        else:
            show_error(f"Could not finish order {order_id}")
            raise typer.Exit(1)
    except FastRecvSMSError as e:
        show_error(str(e))
        raise typer.Exit(1)


@config_app.command("set-key")
def config_set_key(
    provider: str = typer.Argument(help="Provider name (5sim, sms-activate)."),
    key: str = typer.Argument(help="Your API key."),
):
    """Store an API key for a provider."""
    if provider not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        show_error(f"Unknown provider: {provider}. Available: {available}")
        raise typer.Exit(1)
    cfg = Config()
    cfg.set_api_key(provider, key)
    show_success(f"API key saved for {provider}")


@config_app.command("set-default")
def config_set_default(
    provider: str = typer.Argument(help="Provider to use by default."),
):
    """Set the default SMS provider."""
    if provider not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        show_error(f"Unknown provider: {provider}. Available: {available}")
        raise typer.Exit(1)
    cfg = Config()
    cfg.default_provider = provider
    show_success(f"Default provider set to {provider}")


@config_app.command("show")
def config_show():
    """Display current configuration."""
    cfg = Config()
    console.print(render_config_panel(cfg))


@config_app.command("path")
def config_path():
    """Show config file location."""
    from fastrecvsms.config import CONFIG_FILE

    console.print(f"[dim]Config:[/dim] {CONFIG_FILE}")


def _wait_for_sms(provider, order_id: int, timeout: int = 600):
    cfg = Config()
    poll_interval = cfg.poll_interval
    elapsed = 0
    order = None

    try:
        with Live(console=console, refresh_per_second=2) as live:
            while elapsed < timeout:
                order = provider.check_order(order_id)
                live.update(render_order_panel(order, elapsed=elapsed, waiting=True))

                if order.status == OrderStatus.RECEIVED:
                    break

                if order.status in (
                    OrderStatus.CANCELED,
                    OrderStatus.TIMEOUT,
                    OrderStatus.BANNED,
                ):
                    break

                for _ in range(poll_interval):
                    if elapsed >= timeout:
                        break
                    time.sleep(1)
                    elapsed += 1
                    live.update(
                        render_order_panel(order, elapsed=elapsed, waiting=True)
                    )

    except KeyboardInterrupt:
        console.print(f"\n[yellow]Interrupted[/yellow]")
        if typer.confirm("Cancel this order?", default=False):
            try:
                provider.cancel_order(order_id)
                show_success("Order canceled")
            except FastRecvSMSError:
                show_error("Failed to cancel order")
        else:
            console.print(
                f"[dim]Resume: fastrecvsms check {order_id} --wait[/dim]"
            )
        raise typer.Exit()

    if order and order.status == OrderStatus.RECEIVED:
        if order.sms_code:
            console.print(f"\n[bold green]>>> Code: {order.sms_code}[/bold green]")
        if order.sms_text and order.sms_text != order.sms_code:
            console.print(f"[dim]SMS: {order.sms_text}[/dim]")
        console.print()
        console.bell()
        return

    if order and order.status in (
        OrderStatus.CANCELED,
        OrderStatus.TIMEOUT,
        OrderStatus.BANNED,
    ):
        show_error(f"Order status: {order.status.value}")
        raise typer.Exit(1)

    show_error(f"Timed out after {timeout}s waiting for SMS")
    console.print(f"[dim]Resume: fastrecvsms check {order_id} --wait[/dim]")
    raise typer.Exit(1)
