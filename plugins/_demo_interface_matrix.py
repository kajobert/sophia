#!/usr/bin/env python3
"""
SOPHIA - Matrix Terminal Interface
===================================
"Follow the white rabbit..." 🐰

GREEN RAIN AESTHETIC - Pro Roberta
Inspired by: The Matrix (1999)
Theme: Digital rain, green monochrome, glitch effects
"""

import asyncio
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from plugins.base_plugin import BasePlugin


class InterfaceTerminalMatrix(BasePlugin):
    """
    MATRIX TERMINAL INTERFACE - REAL SCI-FI!

    ╔══════════════════════════════════════════════════╗
    ║ MATRIX-AI v3.14 │ 1,500tok │ $0.02 │ 2.1s      ║  <- FIXED HEADER
    ╠══════════════════════════════════════════════════╣
    ║ > Processing neural pathways...                  ║  <- LIVE LOG
    ║ > Analyzing quantum states...                    ║
    ║ > Decoding Matrix protocols...                   ║
    ║ > Response ready                                 ║
    ╚══════════════════════════════════════════════════╝

    Features:
    - Fixed position status bar (always visible)
    - Live updating log area (4 lines)
    - All green monochrome
    - Real-time streaming
    """

    @property
    def name(self) -> str:
        return "interface_terminal_matrix"

    @property
    def plugin_type(self) -> str:
        return "interface"

    @property
    def version(self) -> str:
        return "1.0.0"

    def __init__(self):
        super().__init__()
        self.plugin_name = "interface_terminal_matrix"

        # Force green colors - NO WHITE!
        self.console = Console(force_terminal=True, color_system="truecolor", legacy_windows=False)

        # Matrix green palette (ONLY GREEN!)
        self.colors = {
            "primary": "green",  # #00FF00
            "bright": "bright_green",  # Bright green
            "dim": "color(34)",  # Dark green RGB(0,128,0)
            "bg": "black",  # Black background
        }

        # Metrics
        self.message_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.response_times = []
        self.current_model = "MATRIX-AI-v3.14"

        # Live log (last 4 lines)
        self.live_log: List[str] = []
        self.max_log_lines = 4

    def setup(self, config: Dict[str, Any]):
        """Setup Matrix interface with config."""
        self._display_matrix_boot()
        return True

    def _add_to_log(self, message: str):
        """Add message to live log (keeps only last 4 lines)."""
        self.live_log.append(message)
        if len(self.live_log) > self.max_log_lines:
            self.live_log.pop(0)

    def _create_header(self) -> Table:
        """Create fixed header with status."""
        table = Table.grid(padding=0)
        table.add_column(style="bright_green", justify="left")

        avg_time = (
            sum(self.response_times[-10:]) / len(self.response_times[-10:])
            if self.response_times
            else 0
        )

        status_text = Text()
        status_text.append("● ", style="bold green")
        status_text.append(f"{self.current_model}", style="green")
        status_text.append(" │ ", style="color(34)")
        status_text.append(f"{self.total_tokens:,}tok", style="bright_green")
        status_text.append(" │ ", style="color(34)")
        status_text.append(f"${self.total_cost:.4f}", style="green")
        status_text.append(" │ ", style="color(34)")
        status_text.append(f"{avg_time:.1f}s", style="green")

        table.add_row(status_text)
        return table  # No panel, just text

    def _create_log_panel(self) -> Text:
        """Create live log text (last 4 lines, no panel)."""
        log_text = Text()

        for i, line in enumerate(self.live_log):
            prefix = ">" if i == len(self.live_log) - 1 else " "
            log_text.append(
                f" {prefix} {line}\n",
                style="green" if i == len(self.live_log) - 1 else "color(34)",
            )

        # Fill remaining lines
        for _ in range(self.max_log_lines - len(self.live_log)):
            log_text.append("  ...\n", style="color(34)")

        return log_text  # No panel

    def _display_matrix_boot(self):
        """Display Matrix-style boot sequence - simple green text, no boxes!"""
        self.console.print()
        self.console.print("[bold bright_green]WAKE UP, NEO...[/]")
        self.console.print("[green]THE MATRIX HAS YOU[/]")
        self.console.print("[bright_green]FOLLOW THE WHITE RABBIT...[/]")
        self.console.print()
        self.console.print("[color(34)]> Initializing AI Consciousness...[/]")
        self.console.print("[color(34)]> Connecting to the real world...[/]")
        self.console.print()

    def display_live_system(self, duration: float = 5.0):
        """
        Display live updating system with fixed header and scrolling log.

        This is the REAL Matrix experience!
        """
        import random

        neural_activities = [
            "Scanning quantum entanglement...",
            "Processing neural pathways...",
            "Analyzing matrix protocols...",
            "Decoding encrypted channels...",
            "Synchronizing consciousness...",
            "Calibrating reality filters...",
            "Optimizing thought patterns...",
            "Establishing secure connection...",
        ]

        layout = Layout()
        layout.split_column(Layout(name="header", size=5), Layout(name="log", size=8))

        with Live(layout, console=self.console, refresh_per_second=10) as live:
            start = time.time()
            while time.time() - start < duration:
                # Update log
                self._add_to_log(random.choice(neural_activities))

                # Update layout
                layout["header"].update(self._create_header())
                layout["log"].update(self._create_log_panel())

                time.sleep(0.5)

    def display_message(self, role: str, content: str, **kwargs):
        """Display message in Matrix style - ALL GREEN!"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        text = Text()
        text.append(f"[{timestamp}] ", style="color(34)")

        if role.upper() == "USER" or role.upper() == "YOU":
            text.append("YOU: ", style="bold bright_green")
        elif role.upper() in ["SOPHIA", "ASSISTANT", "AI"]:
            text.append("SOPHIA: ", style="bold green")
        elif role.upper() == "SYSTEM":
            text.append("SYSTEM: ", style="color(34)")
        else:
            text.append(f"{role.upper()}: ", style="green")

        text.append(content, style="green")

        self.console.print(text)

    def display_thinking(self, messages: List[str], duration: float = 3.0):
        """
        Display thinking process with live updates.
        Shows neural activity while AI is processing.
        """
        layout = Layout()
        layout.split_column(Layout(name="header", size=5), Layout(name="log", size=8))

        self.live_log = []  # Clear log

        with Live(layout, console=self.console, refresh_per_second=4) as live:
            for msg in messages:
                self._add_to_log(msg)
                layout["header"].update(self._create_header())
                layout["log"].update(self._create_log_panel())
                time.sleep(duration / len(messages))

        self.console.print()

    def _print_status_bar(self):
        """Print Matrix-style status bar (single line)."""
        avg_time = (
            sum(self.response_times[-10:]) / len(self.response_times[-10:])
            if self.response_times
            else 0
        )

        status = Text()
        status.append("⚫", style="bold green")
        status.append(" │ ", style="dim green")
        status.append(f"{self.current_model}", style="green")
        status.append(" │ ", style="dim green")
        status.append(f"{self.total_tokens:,}tok", style="bright_green")
        status.append(" │ ", style="dim green")
        status.append(f"${self.total_cost:.4f}", style="green")
        status.append(" │ ", style="dim green")
        status.append(f"{self.message_count}msg", style="bright_green")
        status.append(" │ ", style="dim green")
        status.append(f"{avg_time:.1f}s", style="green")

        self.console.print(status)

    def display_message(self, role: str, content: str, **kwargs):
        """Display message in Matrix style."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if role.upper() == "USER" or role.upper() == "YOU":
            prefix = f"[dim green][{timestamp}][/] [bold bright_green]YOU:[/]"
        elif role.upper() in ["SOPHIA", "ASSISTANT", "AI"]:
            prefix = f"[dim green][{timestamp}][/] [bold green]SOPHIA:[/]"
        elif role.upper() == "SYSTEM":
            prefix = f"[dim green][{timestamp}][/] [green]SYSTEM:[/]"
        else:
            prefix = f"[dim green][{timestamp}][/] [green]{role.upper()}:[/]"

        self.console.print(f"{prefix} [green]{content}[/]")

    def display_message_stream(self, role: str, content_generator, **kwargs):
        """Display streaming message with Matrix digital rain effect."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if role.upper() in ["SOPHIA", "ASSISTANT", "AI"]:
            prefix = f"[dim green][{timestamp}][/] [bold green]SOPHIA:[/]"
        else:
            prefix = f"[dim green][{timestamp}][/] [green]{role.upper()}:[/]"

        # Thinking spinner with Matrix characters
        with self.console.status(
            "[bold green]⣿⣿⣿[/] [green]SOPHIA:[/] [dim green]decoding the Matrix...[/]",
            spinner="dots",
        ) as status:
            time.sleep(2)

        # Stream the response
        self.console.print(prefix, end=" ")

        full_response = ""
        for chunk in content_generator:
            self.console.print(f"[green]{chunk}[/]", end="")
            full_response += chunk
            time.sleep(0.03)

        self.console.print()

        # Update metrics
        self.message_count += 1
        self.total_tokens += kwargs.get("tokens", 500)
        self.total_cost += kwargs.get("cost", 0.001)
        self.response_times.append(kwargs.get("response_time", 2.0))

        # Status bar
        self._print_status_bar()

    def display_code(self, code: str, language: str = "python", title: str = "CODE"):
        """Display code with Matrix styling."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)

        panel = Panel(
            syntax,
            title=f"[bold green]▸ {title} ◂[/]",
            border_style="green",
            box=box.MINIMAL,
            padding=(0, 1),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def display_progress(self) -> Progress:
        """Return Matrix-style progress bar."""
        return Progress(
            SpinnerColumn(spinner_name="dots", style="bold green"),
            TextColumn("[green]{task.description}[/]"),
            BarColumn(bar_width=None, style="green", complete_style="bright_green"),
            TextColumn("[bright_green]{task.completed}/{task.total}[/]"),
            TimeElapsedColumn(),
            console=self.console,
        )

    def display_multi_step_progress(self) -> Progress:
        """Return Matrix-style multi-step progress."""
        return Progress(
            TextColumn("[dim green]▸[/] [green]{task.description}[/]"),
            BarColumn(style="green", complete_style="bright_green"),
            TextColumn("[bright_green]{task.completed}/{task.total}[/]"),
            console=self.console,
        )

    def stream_text(self, text: str, delay: float = 0.03):
        """Stream text character by character (synchronous)."""
        for char in text:
            self.console.print(f"[green]{char}[/]", end="")
            time.sleep(delay)
        self.console.print()

    async def stream_text_async(self, text: str, delay: float = 0.03):
        """Stream text character by character (asynchronous)."""
        for char in text:
            self.console.print(f"[green]{char}[/]", end="")
            await asyncio.sleep(delay)
        self.console.print()

    def get_user_input(self, prompt: str = "Enter command") -> str:
        """Get user input with Matrix styling and blinking cursor."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Show blinking cursor prompt
        prompt_text = f"[dim green][{timestamp}][/] [bold bright_green]YOU[/] [green]▌[/]"

        try:
            user_input = Prompt.ask(prompt_text)
            return user_input
        except:
            # Fallback without Rich
            return input(f"[{timestamp}] YOU ▌ ")

    def display_error(self, message: str):
        """Display error in Matrix style (still green!)."""
        self.console.print(f"\n[bold green]⚠[/] [green]ERROR: {message}[/]\n")

    def display_success(self, message: str):
        """Display success message."""
        self.console.print(f"\n[bold bright_green]✓[/] [green]{message}[/]\n")

    async def execute(self, context):
        """
        Plugin execution (interface plugin - non-blocking input check).
        
        AMI 1.0 FIX: Changed from execute(self, **kwargs) to execute(self, context)
        to match BasePlugin contract and prevent TypeError.
        """
        # Interface plugins handle input asynchronously
        # No active input check needed for Matrix terminal
        return {"status": "matrix_interface_active"}


async def demo():
    """Demo všech Matrix features."""
    interface = InterfaceTerminalMatrix()
    interface.setup({})

    print("\n")
    interface.console.print("[bold green]═" * 35 + "[/]")
    interface.console.print("[bold bright_green]  MATRIX TERMINAL - Feature Demo  [/]")
    interface.console.print("[bold green]═" * 35 + "[/]")
    print("\n")

    # Feature 1: Progress Bar
    interface.console.print("[bold bright_green]📥 Feature 1: Matrix Digital Rain Progress[/]\n")

    with interface.display_progress() as progress:
        task = progress.add_task("[green]Downloading red pill...", total=100)
        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(task, advance=1)

    interface.display_success("Red pill downloaded!")

    # Feature 2: Multi-Step Progress
    interface.console.print("\n[bold bright_green]🎯 Feature 2: Matrix Code Compilation[/]\n")

    steps = [
        ("Loading Matrix core", 1),
        ("Initializing green code", 1),
        ("Compiling reality.exe", 1),
        ("Connecting to Zion", 1),
        ("System online", 1),
    ]

    with interface.display_multi_step_progress() as progress:
        for i, (desc, total) in enumerate(steps, 1):
            task = progress.add_task(f"Step {i}/{len(steps)}: {desc}", total=total)
            await asyncio.sleep(0.5)
            progress.update(task, advance=1)

    interface.display_success("All systems operational!")

    # Feature 3: Streaming Text
    interface.console.print("\n[bold bright_green]⚡ Feature 3: Matrix Message Stream[/]\n")

    interface.console.print("[dim green][20:45:30][/] [bold green]MORPHEUS:[/] ", end="")
    await interface.stream_text_async(
        "What if I told you... that you could stream text character by character?", delay=0.02
    )

    # Feature 4: Interactive Input
    interface.console.print("\n[bold bright_green]💬 Feature 4: Matrix Command Input[/]\n")

    interface.console.print(
        "[dim green][20:45:32][/] [bold bright_green]YOU:[/] [green]Red pill or blue pill?[/]"
    )

    # Feature 5: Thinking Spinner + Status
    interface.console.print("\n[bold bright_green]🌀 Feature 5: Neural Processing + Status[/]\n")

    def response_gen():
        response = (
            "The choice is yours, Neo. But remember - all I'm offering is the truth, nothing more."
        )
        for char in response:
            yield char

    interface.current_model = "MATRIX-AI-v3.14"
    interface.display_message_stream(
        "SOPHIA", response_gen(), tokens=1500, cost=0.0234, response_time=2.1
    )

    # Final: Code Display
    interface.console.print("\n[bold bright_green]💻 Feature 6: Matrix Code Display[/]\n")

    code_sample = '''def free_your_mind():
    """There is no spoon."""
    while True:
        reality = question_everything()
        if reality.is_illusion():
            break
        choose_red_pill()
    return "Welcome to the real world"'''

    interface.display_code(code_sample, "python", "REALITY.PY")

    interface.console.print("[bold green]═" * 35 + "[/]")
    interface.console.print("[bold bright_green]  ✓ Matrix Demo Complete!  [/]")
    interface.console.print("[dim green]  'I know kung fu.' - Neo  [/]")
    interface.console.print("[bold green]═" * 35 + "[/]\n")


if __name__ == "__main__":
    asyncio.run(demo())
