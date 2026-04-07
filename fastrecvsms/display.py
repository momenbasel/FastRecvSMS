from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from fastrecvsms.models import Balance, Order, OrderStatus, ServiceInfo

console = Console()

_STATUS_COLORS = {
    OrderStatus.PENDING: "yellow",
    OrderStatus.RECEIVED: "green",
    OrderStatus.CANCELED: "red",
    OrderStatus.TIMEOUT: "red",
    OrderStatus.FINISHED: "blue",
    OrderStatus.BANNED: "red",
}

_STATUS_LABELS = {
    OrderStatus.PENDING: "PENDING",
    OrderStatus.RECEIVED: "RECEIVED",
    OrderStatus.CANCELED: "CANCELED",
    OrderStatus.TIMEOUT: "TIMEOUT",
    OrderStatus.FINISHED: "FINISHED",
    OrderStatus.BANNED: "BANNED",
}


def format_phone(phone: str) -> str:
    if not phone:
        return "N/A"
    cleaned = phone.strip().lstrip("+")
    return f"+{cleaned}"


def format_elapsed(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def show_error(message: str):
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_success(message: str):
    console.print(f"[bold green]{message}[/bold green]")


def render_balance_panel(balance: Balance) -> Panel:
    grid = Table.grid(padding=(0, 3))
    grid.add_column(style="dim", width=12)
    grid.add_column(style="bold")

    grid.add_row("Provider", balance.provider)
    grid.add_row("Balance", f"[green]{balance.amount:,.2f} {balance.currency}[/green]")

    return Panel(grid, title="Account Balance", border_style="cyan", padding=(1, 3))


def render_services_table(services: list[ServiceInfo], country: str = "any") -> Panel:
    if not services:
        return Panel(
            "[dim]No services found[/dim]",
            title="Services",
            border_style="yellow",
            padding=(1, 3),
        )

    table = Table(
        show_header=True,
        header_style="bold",
        border_style="dim",
        padding=(0, 2),
        expand=True,
    )
    table.add_column("Service", style="white", min_width=16)
    table.add_column("Available", justify="right", min_width=10)
    table.add_column("Price", justify="right", min_width=10)

    for svc in services:
        if svc.quantity >= 100:
            qty_style = "green"
        elif svc.quantity >= 10:
            qty_style = "yellow"
        else:
            qty_style = "red"

        qty_text = f"[{qty_style}]{svc.quantity:,}[/{qty_style}]"
        price_text = f"{svc.price:.2f}" if svc.price > 0 else "[dim]-[/dim]"

        table.add_row(svc.name, qty_text, price_text)

    title = f"Services - {country.title()}" if country != "any" else "Services - All Countries"
    footer = f"[dim]{len(services)} services available[/dim]"

    return Panel(
        Group(table, Text(""), Text.from_markup(footer)),
        title=title,
        border_style="cyan",
        padding=(1, 1),
    )


def render_order_panel(
    order: Order,
    elapsed: int = 0,
    waiting: bool = False,
) -> Panel:
    grid = Table.grid(padding=(0, 3))
    grid.add_column(style="dim", width=12)
    grid.add_column()

    if order.phone:
        grid.add_row("Phone", f"[bold]{format_phone(order.phone)}[/bold]")
    grid.add_row("Service", order.service or "N/A")
    grid.add_row("Country", (order.country or "N/A").title())
    if order.price > 0:
        grid.add_row("Price", f"{order.price:.2f}")
    grid.add_row("Provider", order.provider)

    color = _STATUS_COLORS.get(order.status, "white")
    label = _STATUS_LABELS.get(order.status, order.status.value)

    if waiting and order.status == OrderStatus.PENDING:
        timer = format_elapsed(elapsed)
        status_text = f"[{color}]Waiting for SMS... ({timer})[/{color}]"
    else:
        status_text = f"[{color}]{label}[/{color}]"

    grid.add_row("Status", status_text)

    elements = [grid]

    if order.sms_code and order.status == OrderStatus.RECEIVED:
        code_display = Text(f" {order.sms_code} ", style="bold white on green")
        code_panel = Panel(
            Align.center(code_display),
            title="Verification Code",
            border_style="green",
            padding=(0, 4),
        )
        elements.append(Text(""))
        elements.append(code_panel)

        if order.sms_text and order.sms_text != order.sms_code:
            elements.append(Text(""))
            sms_line = Text()
            sms_line.append("Full SMS: ", style="dim")
            sms_line.append(order.sms_text)
            elements.append(sms_line)

    border_color = "green" if order.status == OrderStatus.RECEIVED else (
        "cyan" if order.status == OrderStatus.PENDING else "red"
    )

    return Panel(
        Group(*elements),
        title=f"Order #{order.id}",
        border_style=border_color,
        padding=(1, 3),
    )


def render_config_panel(cfg) -> Panel:
    grid = Table.grid(padding=(0, 3))
    grid.add_column(style="dim", width=18)
    grid.add_column()

    grid.add_row("Default Provider", cfg.default_provider)
    grid.add_row("Default Country", cfg.default_country)
    grid.add_row("Poll Interval", f"{cfg.poll_interval}s")
    grid.add_row("Max Wait Time", f"{cfg.max_wait_time}s")

    providers_data = cfg.data.get("providers", {})
    grid.add_row("", "")
    grid.add_row("[bold]Providers[/bold]", "")

    for pname, pconfig in providers_data.items():
        key = pconfig.get("api_key", "")
        if key:
            masked = key[:6] + "*" * max(0, len(key) - 10) + key[-4:] if len(key) > 10 else "***"
            grid.add_row(f"  {pname}", f"[green]{masked}[/green]")
        else:
            grid.add_row(f"  {pname}", "[dim]not configured[/dim]")

    from fastrecvsms.config import CONFIG_FILE
    grid.add_row("", "")
    grid.add_row("Config File", f"[dim]{CONFIG_FILE}[/dim]")

    return Panel(grid, title="Configuration", border_style="cyan", padding=(1, 3))
