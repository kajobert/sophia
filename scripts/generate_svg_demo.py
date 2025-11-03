#!/usr/bin/env python3
"""
Generate SVG screenshot of Sophia ultra-futuristic demo for README.
Creates a promotional terminal screenshot in high resolution.
"""

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from datetime import datetime

# Create console for SVG export
console = Console(record=True, width=140, height=45)

def create_status_bar():
    """Create status bar with LEDs."""
    status = Text()
    status.append("● ", style="bold green")
    status.append("PWR ", style="bright_white")
    status.append(" │ ", style="dim white")
    status.append("● ", style="bold cyan")
    status.append("CPU ", style="bright_white")
    status.append("12.3% ", style="bright_cyan")
    status.append(" │ ", style="dim white")
    status.append("● ", style="bold magenta")
    status.append("MEM ", style="bright_white")
    status.append("58.7% ", style="bright_magenta")
    status.append(" │ ", style="dim white")
    status.append("● ", style="bold blue")
    status.append("NET ", style="bright_white")
    status.append(" │ ", style="dim white")
    status.append("● ", style="bold green")
    status.append("JULES:COMPLETED ", style="bold green")
    
    return Panel(
        status,
        title="[bold bright_cyan]⚡ SYSTEM STATUS[/]",
        border_style="bright_cyan",
        box=box.HEAVY,
        height=3
    )

def create_conversation():
    """Create sample conversation."""
    conv = Text()
    
    # User message 1
    conv.append("╭─ [10:30:45] ", style="dim cyan")
    conv.append("👤 YOU\n", style="bold yellow")
    conv.append("│ Hello Sophia! Show me the Year 2030 A.M.I. interface.\n", style="white")
    conv.append("╰─\n\n", style="dim cyan")
    
    # Sophia response 1
    conv.append("╭─ [10:30:47] ", style="dim cyan")
    conv.append("🤖 SOPHIA\n", style="bold cyan")
    conv.append("│ Welcome to the Autonomous Mind Interface v2.0! This is the future of AI\n", style="bright_white")
    conv.append("│ collaboration - sticky panels, live metrics, Jules orchestration, and\n", style="bright_white")
    conv.append("│ real-time system monitoring. Everything you need for Year 2030 AI work!\n", style="bright_white")
    conv.append("╰─\n\n", style="dim cyan")
    
    # User message 2
    conv.append("╭─ [10:30:52] ", style="dim cyan")
    conv.append("👤 YOU\n", style="bold yellow")
    conv.append("│ What makes this interface special?\n", style="white")
    conv.append("╰─\n\n", style="dim cyan")
    
    # Sophia response 2
    conv.append("╭─ [10:30:54] ", style="dim cyan")
    conv.append("🤖 SOPHIA\n", style="bold cyan")
    conv.append("│ Three groundbreaking features:\n", style="bright_white")
    conv.append("│ • UV/Docker-style sticky panels that NEVER flicker\n", style="bright_white")
    conv.append("│ • Multi-agent Jules orchestration (100 free sessions/day)\n", style="bright_white")
    conv.append("│ • Real-time metrics with color-coded priority indicators\n", style="bright_white")
    conv.append("│\n", style="bright_white")
    conv.append("│ This isn't just a terminal - it's a collaborative AI workspace! 🚀\n", style="bright_white")
    conv.append("╰─\n", style="dim cyan")
    
    return Panel(
        conv,
        title="[bold bright_white]💬 CONVERSATION[/]",
        border_style="bright_white",
        box=box.ROUNDED,
        padding=(1, 2)
    )

def create_metrics():
    """Create metrics panel."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim white", justify="left")
    table.add_column(style="bright_white", justify="right")
    
    table.add_row("💎 Tokens:", "2,847")
    table.add_row("💰 Cost:", "$0.0068")
    table.add_row("💬 Messages:", "4")
    table.add_row("", "")
    table.add_row("─" * 12, "─" * 8)
    table.add_row("", "")
    table.add_row("🔥 CPU:", Text("12.3%", style="bright_green"))
    table.add_row("🧠 Memory:", Text("58.7%", style="bright_yellow"))
    
    return Panel(
        table,
        title="[bold bright_yellow]📊 LIVE METRICS[/]",
        border_style="bright_yellow",
        box=box.ROUNDED,
        height=12
    )

def create_jules():
    """Create Jules monitor."""
    content = Table.grid(padding=0)
    content.add_column()
    
    state_line = Text()
    state_line.append("● ", style="bold green")
    state_line.append("COMPLETED", style="bold green")
    content.add_row(state_line)
    content.add_row(Text("ID: ...79433435", style="dim cyan"))
    content.add_row(Text("Branch: nomad/tui-fix", style="dim magenta"))
    content.add_row(Text(""))
    
    quota_line = Text()
    quota_line.append("📊 Quota: ", style="bright_white")
    quota_line.append("18", style="bright_cyan")
    quota_line.append("/100", style="dim white")
    content.add_row(quota_line)
    
    bar = Text()
    bar.append("███", style="bright_cyan")
    bar.append("░░░░░░░░░░░░░░░", style="dim white")
    content.add_row(bar)
    
    return Panel(
        content,
        title="[bold bright_green]🤖 JULES ASYNC[/]",
        border_style="bright_green",
        box=box.ROUNDED,
        height=12
    )

def create_logs():
    """Create activity log."""
    content = Text()
    content.append("⚙️ ", style="cyan")
    content.append("10:30:45 ", style="dim white")
    content.append("User message received\n", style="cyan")
    
    content.append("⚙️ ", style="cyan")
    content.append("10:30:46 ", style="dim white")
    content.append("Generating response...\n", style="cyan")
    
    content.append("⚙️ ", style="cyan")
    content.append("10:30:49 ", style="dim white")
    content.append("Response completed\n", style="cyan")
    
    content.append("⚙️ ", style="cyan")
    content.append("10:30:52 ", style="dim white")
    content.append("User query received\n", style="cyan")
    
    content.append("⚙️ ", style="cyan")
    content.append("10:30:53 ", style="dim white")
    content.append("Analyzing features...\n", style="cyan")
    
    content.append("✓ ", style="bold green")
    content.append("10:30:56 ", style="dim white")
    content.append("All systems optimal\n", style="bold green")
    
    return Panel(
        content,
        title="[bold bright_blue]⚙️ ACTIVITY STREAM[/]",
        border_style="bright_blue",
        box=box.ROUNDED
    )

def create_footer():
    """Create footer."""
    footer = Text()
    footer.append("🕐 2025-11-04 10:31:00 ", style="dim cyan")
    footer.append("│ ", style="dim white")
    footer.append("v2.0 ", style="dim white")
    footer.append("│ ", style="dim white")
    footer.append("Uptime: 15m", style="dim green")
    
    return Panel(
        footer,
        border_style="dim white",
        box=box.ROUNDED,
        height=3
    )

# Create layout
layout = Layout()

layout.split_column(
    Layout(name="status_bar", size=3),
    Layout(name="main_content", ratio=1),
    Layout(name="footer", size=3)
)

layout["main_content"].split_row(
    Layout(name="conversation", ratio=7),
    Layout(name="sidebar", ratio=3)
)

layout["sidebar"].split_column(
    Layout(name="metrics", size=12),
    Layout(name="jules", size=12),
    Layout(name="logs", ratio=1)
)

# Populate layout
layout["status_bar"].update(create_status_bar())
layout["conversation"].update(create_conversation())
layout["metrics"].update(create_metrics())
layout["jules"].update(create_jules())
layout["logs"].update(create_logs())
layout["footer"].update(create_footer())

# Print to console (recording)
console.print(layout)

# Export to SVG
svg_output = console.export_svg(
    title="Sophia A.M.I. - Year 2030 Autonomous Mind Interface",
    clear=False
)

# Save to file
output_file = "docs/assets/sophia-demo-screenshot.svg"
with open(output_file, "w") as f:
    f.write(svg_output)

print(f"✅ SVG screenshot saved to: {output_file}")
print(f"   Size: {len(svg_output)} bytes")
print(f"   Resolution: 140x45 characters")
print(f"\n🎨 Perfect for GitHub README promotional section!")
