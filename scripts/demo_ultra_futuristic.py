#!/usr/bin/env python3
"""
🚀 SOPHIA A.M.I. - ULTRA FUTURISTIC DEMO (Year 2030 Style)
=============================================================
Ultimate demonstration of sticky panels, status bars, live metrics,
LED indicators, color-coded priorities, and professional AI UX.

This is the TARGET UX we're aiming for in production!
"""

import asyncio
import time
import psutil
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich import box
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.align import Align

console = Console()

# 🎨 ULTRA COLOR PALETTE - Intuitive and professional
NEON_CYAN = "bright_cyan"
NEON_MAGENTA = "bright_magenta"
NEON_GREEN = "bright_green"
NEON_YELLOW = "bright_yellow"
ELECTRIC_BLUE = "bright_blue"
WARNING_ORANGE = "yellow"
ERROR_RED = "red"
SUCCESS_GREEN = "green"
DIM_GRAY = "dim white"

# 🎨 SOPHIA ULTRA COMPACT ASCII LOGO
SOPHIA_ULTRA_LOGO = """
╔═════════════════════════════════════════════════════════════════════╗
║  ███████╗ ██████╗ ██████╗ ██╗  ██╗██╗ █████╗     A.M.I. v2.0        ║
║  ██╔════╝██╔═══██╗██╔══██╗██║  ██║██║██╔══██╗    AUTONOMOUS MIND    ║
║  ███████╗██║   ██║██████╔╝███████║██║███████║    INTERFACE          ║
║  ╚════██║██║   ██║██╔═══╝ ██╔══██║██║██╔══██║    Status: ● ACTIVE   ║
║  ███████║╚██████╔╝██║     ██║  ██║██║██║  ██║    2025-11-04 00:00   ║
║  ╚══════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝                       ║
╚═════════════════════════════════════════════════════════════════════╝
"""


def get_system_metrics():
    """Get real CPU and memory metrics using psutil."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        return cpu, mem
    except:
        return 0.0, 0.0


def create_status_bar(
    cpu_percent: float = 0,
    mem_percent: float = 0,
    network_active: bool = True,
    jules_state: str = "IDLE",
) -> Panel:
    """Create fixed top status bar with LED indicators and system metrics."""
    status = Text()

    # Power LED (always ON)
    status.append("● ", style="bold green")
    status.append("PWR ", style="bright_white")
    status.append(" │ ", style="dim white")

    # CPU indicator with live percentage
    status.append("● ", style="bold cyan")
    status.append("CPU ", style="bright_white")
    status.append(f"{cpu_percent:>4.1f}% ", style="bright_cyan")
    status.append(" │ ", style="dim white")

    # Memory indicator with live percentage
    status.append("● ", style="bold magenta")
    status.append("MEM ", style="bright_white")
    status.append(f"{mem_percent:>4.1f}% ", style="bright_magenta")
    status.append(" │ ", style="dim white")

    # Network indicator
    net_style = "bold blue" if network_active else "dim"
    status.append("● ", style=net_style)
    status.append("NET ", style="bright_white" if network_active else "dim white")
    status.append(" │ ", style="dim white")

    # Jules worker state indicator
    if jules_state == "IDLE":
        jules_led = "⭘"
        jules_style = "dim white"
    elif jules_state == "WORKING":
        jules_led = "◐"
        jules_style = "bold yellow"
    else:  # COMPLETED
        jules_led = "●"
        jules_style = "bold green"

    status.append(f"{jules_led} ", style=jules_style)
    status.append(f"JULES:{jules_state} ", style=jules_style)

    return Panel(
        status,
        title="[bold bright_cyan]⚡ SYSTEM STATUS[/]",
        border_style="bright_cyan",
        box=box.HEAVY,
        padding=(0, 1),
        height=3,
    )


def create_footer(version: str = "2.0", uptime: str = "0m") -> Panel:
    """Create fixed bottom footer with timestamp and version."""
    footer = Text()
    footer.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ", style="dim cyan")
    footer.append("│ ", style="dim white")
    footer.append(f"v{version} ", style="dim white")
    footer.append("│ ", style="dim white")
    footer.append(f"Uptime: {uptime}", style="dim green")

    return Panel(Align.center(footer), border_style="dim white", box=box.ROUNDED, height=3)


def create_metrics_panel(
    tokens: int = 0, cost: float = 0.0, messages: int = 0, cpu: float = 0, mem: float = 0
) -> Panel:
    """Create live metrics panel with token usage and system resources."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim white", justify="left")
    table.add_column(style="bright_white", justify="right")

    # Token metrics
    table.add_row("💎 Tokens:", f"{tokens:,}")
    table.add_row("💰 Cost:", f"${cost:.4f}")
    table.add_row("💬 Messages:", f"{messages}")

    # Separator
    table.add_row("", "")
    table.add_row("─" * 12, "─" * 8)
    table.add_row("", "")

    # System metrics with color coding
    cpu_style = "bright_red" if cpu > 80 else "bright_yellow" if cpu > 50 else "bright_green"
    mem_style = "bright_red" if mem > 80 else "bright_yellow" if mem > 50 else "bright_green"

    table.add_row("🔥 CPU:", Text(f"{cpu:.1f}%", style=cpu_style))
    table.add_row("🧠 Memory:", Text(f"{mem:.1f}%", style=mem_style))

    return Panel(
        table,
        title="[bold bright_yellow]📊 LIVE METRICS[/]",
        border_style="bright_yellow",
        box=box.ROUNDED,
        padding=(0, 0),
        height=12,
    )


def create_jules_panel(
    state: str = "IDLE",
    quota_used: int = 15,
    quota_total: int = 100,
    session_id: str = "",
    branch: str = "",
) -> Panel:
    """Create Jules worker monitor with session tracking and progress bar."""
    content = Table.grid(padding=0)
    content.add_column()

    # State indicator with icon
    state_line = Text()
    if state == "IDLE":
        state_line.append("⭘ ", style="dim white")
        state_line.append("IDLE", style="dim white")
    elif state == "WORKING":
        state_line.append("◐ ", style="bold yellow")
        state_line.append("WORKING", style="bold yellow")
    else:  # COMPLETED
        state_line.append("● ", style="bold green")
        state_line.append("COMPLETED", style="bold green")
    content.add_row(state_line)

    # Session info (if active)
    if session_id:
        content.add_row(Text(f"ID: ...{session_id[-8:]}", style="dim cyan"))

    # Branch info (if working)
    if branch:
        content.add_row(Text(f"Branch: {branch}", style="dim magenta"))

    # Separator
    content.add_row(Text(""))

    # Quota bar
    quota_line = Text()
    quota_line.append("📊 Quota: ", style="bright_white")
    quota_line.append(f"{quota_used}", style="bright_cyan")
    quota_line.append(f"/{quota_total}", style="dim white")
    content.add_row(quota_line)

    # Progress bar (visual quota indicator)
    progress_width = 18
    filled = int((quota_used / quota_total) * progress_width)
    bar = Text()
    bar.append("█" * filled, style="bright_cyan")
    bar.append("░" * (progress_width - filled), style="dim white")
    content.add_row(bar)

    return Panel(
        content,
        title="[bold bright_green]🤖 JULES ASYNC[/]",
        border_style="bright_green",
        box=box.ROUNDED,
        padding=(0, 1),
        height=12,
    )


def create_activity_log(logs: list) -> Panel:
    """Create activity stream panel with color-coded priority."""
    content = Text()

    if not logs:
        content.append("⏳ Waiting for activity...", style="dim")
    else:
        for timestamp, level, message in logs[-15:]:  # Last 15 entries
            # Icon and color based on level
            if level == "INFO":
                icon = "⚙️"
                style = "cyan"
            elif level == "WARNING":
                icon = "⚠️"
                style = "yellow"
            elif level == "ERROR":
                icon = "❌"
                style = "red"
            else:  # DEBUG
                icon = "🔍"
                style = "dim cyan"

            content.append(f"{icon} ", style=style)
            content.append(f"{timestamp} ", style="dim white")
            content.append(f"{message}\n", style=style)

    return Panel(
        content,
        title="[bold bright_blue]⚙️ ACTIVITY STREAM[/]",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(0, 1),
    )


def create_conversation_panel(conversation_text: Text) -> Panel:
    """Create main conversation panel with user/AI messages."""
    return Panel(
        conversation_text if conversation_text else Text("Awaiting neural input...", style="dim"),
        title="[bold bright_white]💬 CONVERSATION[/]",
        border_style="bright_white",
        box=box.ROUNDED,
        padding=(1, 2),
    )


async def boot_sequence():
    """Ultra futuristic boot sequence with progress bars."""
    console.clear()
    console.print(SOPHIA_ULTRA_LOGO, style="bold cyan")
    await asyncio.sleep(1.5)

    console.print("\n[bold cyan][BEEP][/bold cyan] Initializing Autonomous Mind Interface...")
    await asyncio.sleep(0.8)

    # Progress bars for each component
    with Progress(
        SpinnerColumn(spinner_name="dots12", style="bold cyan"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, style="cyan", complete_style="bold green"),
        TextColumn("[bold green]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:

        # Neural cores
        task1 = progress.add_task("[cyan]Loading neural cores...", total=100)
        for i in range(100):
            await asyncio.sleep(0.015)
            progress.update(task1, advance=1)

        # Network
        task2 = progress.add_task("[cyan]Establishing network...", total=100)
        for i in range(100):
            await asyncio.sleep(0.012)
            progress.update(task2, advance=1)

        # Plugins
        task3 = progress.add_task("[cyan]Loading plugins...", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(task3, advance=1)

        # Jules worker
        task4 = progress.add_task("[cyan]Connecting Jules worker...", total=100)
        for i in range(100):
            await asyncio.sleep(0.011)
            progress.update(task4, advance=1)

        # Local LLM
        task5 = progress.add_task("[cyan]Warming up local LLM...", total=100)
        for i in range(100):
            await asyncio.sleep(0.013)
            progress.update(task5, advance=1)

    console.print("\n[bold green]✓ All systems online[/bold green]")
    await asyncio.sleep(1)


def show_user_message(conversation: Text, message: str):
    """Add user message to conversation."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    conversation.append(f"╭─ [{timestamp}] ", style="dim cyan")
    conversation.append("👤 YOU\n", style="bold yellow")
    conversation.append(f"│ {message}\n", style="white")
    conversation.append("╰─\n\n", style="dim cyan")


async def stream_sophia_response(conversation: Text, response: str):
    """Stream Sophia's response word by word with typing cursor."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    conversation.append(f"╭─ [{timestamp}] ", style="dim cyan")
    conversation.append("🤖 SOPHIA\n", style="bold cyan")
    conversation.append("│ ", style="dim cyan")

    # Word-by-word streaming simulation
    words = response.split()
    for i, word in enumerate(words):
        conversation.append(word + " ", style="bright_white")
        await asyncio.sleep(0.05)  # Simulate typing speed

        # Add cursor effect periodically
        if i % 3 == 0:
            yield  # Allow Live to refresh

    conversation.append("\n╰─\n\n", style="dim cyan")


async def run_demo():
    """Main demo with sticky panels, live updates, and word-by-word streaming."""
    # Boot sequence
    await boot_sequence()

    console.clear()

    # Create ultra-fixed layout
    layout = Layout()

    layout.split_column(
        Layout(name="status_bar", size=3),  # Fixed status bar (LEDs, CPU, MEM)
        Layout(name="main_content", ratio=1),  # Main content area
        Layout(name="footer", size=3),  # Fixed footer (timestamp, version)
    )

    # Main content: conversation (70%) + sidebar panels (30%)
    layout["main_content"].split_row(
        Layout(name="conversation", ratio=7), Layout(name="sidebar", ratio=3)
    )

    # Sidebar: metrics, jules, logs stacked vertically
    layout["sidebar"].split_column(
        Layout(name="metrics", size=12),  # Fixed height for metrics
        Layout(name="jules", size=12),  # Fixed height for Jules
        Layout(name="logs", ratio=1),  # Remaining space for activity log
    )

    # Initialize conversation and activity log
    conversation = Text()
    activity_log = []

    # Metrics state
    tokens = 0
    cost = 0.0
    messages = 0

    # Jules state
    jules_state = "IDLE"
    jules_session = ""
    jules_branch = ""

    start_time = time.time()

    # Start Live display with manual refresh
    with Live(layout, console=console, refresh_per_second=10, screen=False) as live:

        # Demo scenario: 3-message conversation

        # Message 1: User greeting
        cpu, mem = get_system_metrics()
        layout["status_bar"].update(create_status_bar(cpu, mem, True, jules_state))
        layout["footer"].update(create_footer("2.0", "0m"))

        show_user_message(conversation, "Hello Sophia! Show me your futuristic UI.")
        messages += 1
        activity_log.append((datetime.now().strftime("%H:%M:%S"), "INFO", "User message received"))

        layout["conversation"].update(create_conversation_panel(conversation))
        layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
        layout["jules"].update(
            create_jules_panel(jules_state, 15, 100, jules_session, jules_branch)
        )
        layout["logs"].update(create_activity_log(activity_log))

        live.refresh()
        await asyncio.sleep(1)

        # Sophia response 1 - word by word
        response1 = "Absolutely! This is the Year 2030 A.M.I. interface with sticky panels, live metrics, LED indicators, and real-time system monitoring. Notice the fixed status bar at top and footer at bottom!"

        activity_log.append(
            (datetime.now().strftime("%H:%M:%S"), "INFO", "Generating response...")
        )
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        # Stream response word by word
        async for _ in stream_sophia_response(conversation, response1):
            tokens += 50
            cost += 0.0001
            cpu, mem = get_system_metrics()

            layout["conversation"].update(create_conversation_panel(conversation))
            layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
            layout["status_bar"].update(create_status_bar(cpu, mem, True, jules_state))
            live.refresh()

        messages += 1
        tokens += 150
        cost += 0.0005
        activity_log.append((datetime.now().strftime("%H:%M:%S"), "INFO", "Response completed"))

        layout["conversation"].update(create_conversation_panel(conversation))
        layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        await asyncio.sleep(2)

        # Message 2: Ask about Jules
        show_user_message(conversation, "What's the status of Jules async worker?")
        messages += 1
        activity_log.append(
            (datetime.now().strftime("%H:%M:%S"), "INFO", "User query about Jules")
        )

        # Jules becomes WORKING
        jules_state = "WORKING"
        jules_session = "3618428757879433435"
        jules_branch = "nomad/tui-uv-style-fix"

        cpu, mem = get_system_metrics()
        layout["conversation"].update(create_conversation_panel(conversation))
        layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
        layout["status_bar"].update(create_status_bar(cpu, mem, True, jules_state))
        layout["jules"].update(
            create_jules_panel(jules_state, 15, 100, jules_session, jules_branch)
        )
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        await asyncio.sleep(1.5)

        # Sophia response 2
        response2 = "Jules is currently WORKING on the TUI UV-style fix! Session ID ...33435 is active on branch nomad/tui-uv-style-fix. We've used 15 out of 100 free Gemini 2.5 Pro sessions today. The async worker system allows me to delegate complex tasks while maintaining full conversation with you!"

        activity_log.append(
            (datetime.now().strftime("%H:%M:%S"), "INFO", "Checking Jules status...")
        )
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        async for _ in stream_sophia_response(conversation, response2):
            tokens += 60
            cost += 0.00012
            cpu, mem = get_system_metrics()

            layout["conversation"].update(create_conversation_panel(conversation))
            layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
            layout["status_bar"].update(create_status_bar(cpu, mem, True, jules_state))
            live.refresh()

        messages += 1
        tokens += 180
        cost += 0.0006
        activity_log.append((datetime.now().strftime("%H:%M:%S"), "INFO", "Jules status reported"))

        layout["conversation"].update(create_conversation_panel(conversation))
        layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        await asyncio.sleep(2)

        # Message 3: Ask about future vision
        show_user_message(
            conversation, "This looks amazing! Is this really the future of AI interfaces?"
        )
        messages += 1
        activity_log.append((datetime.now().strftime("%H:%M:%S"), "INFO", "User impressed by UI"))

        # Jules completes task
        jules_state = "COMPLETED"

        cpu, mem = get_system_metrics()
        layout["conversation"].update(create_conversation_panel(conversation))
        layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
        layout["status_bar"].update(create_status_bar(cpu, mem, True, jules_state))
        layout["jules"].update(
            create_jules_panel(jules_state, 15, 100, jules_session, jules_branch)
        )
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        await asyncio.sleep(1.5)

        # Sophia response 3 - final vision
        response3 = "Yes! This is exactly how AI interfaces should work in 2030. Sticky panels that never flicker. Real-time metrics. Multi-worker orchestration with Jules. Color-coded priorities. Professional yet futuristic. This isn't just a terminal - it's a collaborative workspace where human creativity meets AI capabilities. And the best part? Tomorrow is our FIRST LEGENDARY BOOT! 🚀"

        activity_log.append(
            (datetime.now().strftime("%H:%M:%S"), "INFO", "Generating final response...")
        )
        activity_log.append(
            (datetime.now().strftime("%H:%M:%S"), "WARNING", "Jules task COMPLETED!")
        )
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        async for _ in stream_sophia_response(conversation, response3):
            tokens += 70
            cost += 0.00014
            cpu, mem = get_system_metrics()

            uptime = f"{int((time.time() - start_time) / 60)}m"
            layout["conversation"].update(create_conversation_panel(conversation))
            layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
            layout["status_bar"].update(create_status_bar(cpu, mem, True, jules_state))
            layout["footer"].update(create_footer("2.0", uptime))
            live.refresh()

        messages += 1
        tokens += 200
        cost += 0.0008
        activity_log.append(
            (datetime.now().strftime("%H:%M:%S"), "INFO", "Conversation completed")
        )
        activity_log.append(
            (datetime.now().strftime("%H:%M:%S"), "INFO", "All panels updated successfully")
        )

        layout["conversation"].update(create_conversation_panel(conversation))
        layout["metrics"].update(create_metrics_panel(tokens, cost, messages, cpu, mem))
        layout["logs"].update(create_activity_log(activity_log))
        live.refresh()

        # Hold final state for viewing
        await asyncio.sleep(15)

    console.print(
        "\n[bold green]✓ Demo completed! This is the TARGET UX for production.[/bold green]"
    )
    console.print("[dim]Press Ctrl+C to exit[/dim]")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
