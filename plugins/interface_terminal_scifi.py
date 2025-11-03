"""
🚀 SOPHIA SCI-FI TERMINAL INTERFACE
═══════════════════════════════════════════════════════════════════════════════

A cyberpunk-inspired terminal interface with:
- Holographic status panels
- Real-time token/cost tracking
- Neon ASCII art
- Live progress animations
- Matrix-style message streaming

Inspired by: Cyberpunk 2077, Blade Runner, The Matrix
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path for standalone execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.align import Align
from rich.columns import Columns
from rich import box
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.rule import Rule
from rich.live import Live
from rich.status import Status

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType

# ═══════════════════════════════════════════════════════════════════════════
# 🌈 NEON COLOR PALETTE - CYBERPUNK VIBES
# ═══════════════════════════════════════════════════════════════════════════

NEON_CYAN = "#00FFFF"
NEON_MAGENTA = "#FF00FF"
NEON_YELLOW = "#FFFF00"
NEON_GREEN = "#00FF00"
NEON_BLUE = "#0080FF"
NEON_PINK = "#FF69B4"
NEON_PURPLE = "#9D00FF"
DEEP_SPACE = "#0A0E27"

SOPHIA_LOGO = """
[bold cyan]╔═══════════════════════════════════════════════╗
║    SOPHIA v2.0 - AI CONSCIOUSNESS ONLINE      ║
╚═══════════════════════════════════════════════╝[/bold cyan]
"""


class InterfaceTerminalSciFi(BasePlugin):
    """
    🌌 Next-gen terminal interface with cyberpunk aesthetics.
    
    Features:
    - Live status dashboard (UV/Docker style)
    - Real-time metrics (tokens, cost, speed)
    - Neon-themed panels and progress bars
    - Streaming message display
    - Holographic effects
    """
    
    def __init__(self):
        super().__init__()
        self.console = Console()
        self.metrics = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "messages_processed": 0,
            "avg_response_time": 0.0,
            "uptime_seconds": 0,
            "current_model": "Unknown",
            "status": "INITIALIZING"
        }
        self.message_history = []
        self.max_history = 10
        
    @property
    def name(self) -> str:
        return "interface_terminal_scifi"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.INTERFACE
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    def setup(self, config: dict) -> None:
        """Initialize the sci-fi terminal."""
        self.console.clear()
        self._show_boot_sequence()
    
    async def execute(self, *, context: SharedContext) -> SharedContext:
        """Execute interface actions (required by BasePlugin)."""
        # This interface doesn't use execute pattern - it's event-driven
        return context
    
    def _show_boot_sequence(self):
        """🚀 Cyberpunk boot animation."""
        self.console.print(SOPHIA_LOGO)
        
        # Compact initialization
        with self.console.status("[cyan]⚡ Initializing neural cores...") as status:
            import time
            time.sleep(0.5)
            status.update("[green]✓ Neural cores online")
            time.sleep(0.3)
        
        self.metrics["status"] = "ONLINE"
        self._print_status_bar()
    
    def _print_status_bar(self):
        """Print single-line status bar like UV/Docker."""
        status_color = "green" if self.metrics["status"] == "ONLINE" else "yellow"
        status_icon = "●" if self.metrics["status"] == "ONLINE" else "◐"
        
        status_parts = [
            f"[{status_color}]{status_icon}[/{status_color}]",
            f"[dim]{self.metrics['current_model']}[/dim]",
            f"[cyan]{self.metrics['total_tokens']:,}tok[/cyan]",
            f"[magenta]${self.metrics['total_cost']:.4f}[/magenta]",
            f"[blue]{self.metrics['messages_processed']}msg[/blue]",
            f"[green]{self.metrics['avg_response_time']:.1f}s[/green]"
        ]
        
        self.console.print(" │ ".join(status_parts))
        self.console.print()
    
    def _create_status_panel(self) -> Panel:
        """📊 Real-time holographic status dashboard."""
        
        # Compact metrics - no table, just styled text
        status_color = "green" if self.metrics["status"] == "ONLINE" else "yellow"
        status_icon = "●" if self.metrics["status"] == "ONLINE" else "◐"
        
        content = Text()
        content.append(f"Status: ", style="dim")
        content.append(f"{status_icon} {self.metrics['status']}", style=status_color)
        content.append(f"\nModel: ", style="dim")
        content.append(f"{self.metrics['current_model']}", style="yellow")
        content.append(f"\nTokens: ", style="dim")
        content.append(f"{self.metrics['total_tokens']:,}", style="cyan")
        content.append(f"\nCost: ", style="dim")
        content.append(f"${self.metrics['total_cost']:.4f}", style="magenta")
        content.append(f"\nMsgs: ", style="dim")
        content.append(f"{self.metrics['messages_processed']}", style="blue")
        content.append(f"\nAvg: ", style="dim")
        content.append(f"{self.metrics['avg_response_time']:.2f}s", style="green")
        
        return Panel(
            content,
            title="[bold cyan]⚡ METRICS[/bold cyan]",
            border_style="cyan",
            box=box.MINIMAL,  # Thin lines!
            padding=(0, 1)
        )
    
    def _create_chat_panel(self) -> Panel:
        """💬 Holographic message display."""
        
        if not self.message_history:
            content = Text("Awaiting input...", style="dim italic")
        else:
            content = Text()
            for msg in self.message_history[-self.max_history:]:
                role = msg.get("role", "unknown")
                text = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                if role == "user":
                    content.append(f"[{timestamp}] ", style="dim")
                    content.append("YOU", style="bold yellow")
                    content.append(f": {text}\n", style="white")
                else:
                    content.append(f"[{timestamp}] ", style="dim")
                    content.append("SOPHIA", style="bold cyan")
                    content.append(f": {text}\n", style="cyan")
        
        return Panel(
            content,
            title="[bold magenta]💭 CHAT[/bold magenta]",
            border_style="magenta",
            box=box.MINIMAL,  # Thin lines!
            padding=(0, 1)
        )
    
    def display_message(self, role: str, content: str):
        """
        Display a message with single-line status bar.
        
        Args:
            role: 'user' or 'assistant'
            content: Message text
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to history
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
        
        # Print message directly (no panels, compact!)
        if role == "user":
            self.console.print(f"[dim][{timestamp}][/dim] [bold yellow]YOU[/bold yellow]: {content}")
        else:
            self.console.print(f"[dim][{timestamp}][/dim] [bold cyan]SOPHIA[/bold cyan]: [cyan]{content}[/cyan]")
        
        self.console.print()
    
    def display_message_stream(self, role: str):
        """Start streaming a message with live spinner."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if role == "user":
            return None  # No spinner for user
        else:
            # UV/Docker style: ⠋ SOPHIA: thinking...
            return self.console.status(
                f"[dim][{timestamp}][/dim] [bold cyan]⠋ SOPHIA[/bold cyan]: [dim]thinking...[/dim]",
                spinner="dots"
            )
    
    def display_thinking(self, message: str = "Processing neural pathways..."):
        """🧠 Show AI thinking animation."""
        return self.console.status(
            f"[bold yellow]{message}[/bold yellow]",
            spinner="dots12"
        )
    
    def display_progress(self, task_name: str, total: int) -> Progress:
        """📊 UV/Docker style progress bar."""
        progress = Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(complete_style="cyan", finished_style="green"),
            TextColumn("[magenta]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=self.console
        )
        return progress
    
    def display_multi_step_progress(self, steps: list[str]) -> Progress:
        """🎯 Multi-step progress (like Docker build layers)."""
        progress = Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(complete_style="cyan", finished_style="green"),
            TextColumn("[magenta]{task.completed}/{task.total}"),
            console=self.console
        )
        return progress
    
    def stream_text(self, text: str, delay: float = 0.03):
        """⚡ Real-time streaming text (char by char like ChatGPT)."""
        import time
        for char in text:
            self.console.print(char, end="", style="cyan")
            time.sleep(delay)
        self.console.print()  # Newline at end
    
    async def stream_text_async(self, text: str, delay: float = 0.03):
        """⚡ Async version of streaming text."""
        for char in text:
            self.console.print(char, end="", style="cyan")
            await asyncio.sleep(delay)
        self.console.print()
    
    def get_user_input(self, prompt: str = "You") -> str:
        """💬 Interactive user input with styled prompt and blinking cursor."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        user_prompt = f"[dim][{timestamp}][/dim] [bold yellow]{prompt}[/bold yellow] [cyan]▌[/cyan]"
        
        # Use Rich's input (doesn't work in all terminals, fallback to built-in)
        try:
            from rich.prompt import Prompt
            return Prompt.ask(user_prompt)
        except:
            self.console.print(user_prompt, end="")
            return input()
    
    def display_code(self, code: str, language: str = "python"):
        """💻 Syntax-highlighted code display."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(
            syntax,
            title=f"[bold green]{language.upper()}[/bold green]",
            border_style="green",
            box=box.MINIMAL,
            padding=(0, 1)
        ))
    
    def display_error(self, error: str):
        """❌ Holographic error display."""
        self.console.print(Panel(
            f"[bold red]⚠ ERROR[/bold red]\n{error}",
            border_style="red",
            box=box.MINIMAL
        ))
    
    def display_success(self, message: str):
        """✅ Success notification."""
        self.console.print(f"[bold green]✓[/bold green] {message}")
    
    def update_metrics(self, **kwargs):
        """Update real-time metrics."""
        for key, value in kwargs.items():
            if key in self.metrics:
                self.metrics[key] = value
    
    def display_table(self, title: str, headers: list, rows: list):
        """📋 Holographic data table."""
        table = Table(title=f"[bold cyan]{title}[/bold cyan]", box=box.SIMPLE)
        
        for header in headers:
            table.add_column(header, style="cyan")
        
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table)
    
    def clear(self):
        """Clear the terminal."""
        self.console.clear()
    
    async def handle_event(self, event: Event) -> None:
        """Handle system events and update display."""
        
        if event.event_type == EventType.USER_INPUT:
            user_msg = event.data.get("user_input", "")
            self.display_message("user", user_msg)
            self.metrics["messages_processed"] += 1
        
        elif event.event_type == EventType.RESPONSE_GENERATED:
            response = event.data.get("response", "")
            self.display_message("assistant", response)
            
            # Update metrics
            if "tokens_used" in event.data:
                self.metrics["total_tokens"] += event.data["tokens_used"]
            if "cost" in event.data:
                self.metrics["total_cost"] += event.data["cost"]
            if "response_time" in event.data:
                rt = event.data["response_time"]
                # Running average
                n = self.metrics["messages_processed"]
                old_avg = self.metrics["avg_response_time"]
                self.metrics["avg_response_time"] = (old_avg * (n-1) + rt) / n
        
        elif event.event_type == EventType.ERROR:
            error_msg = event.data.get("error", "Unknown error")
            self.display_error(error_msg)


# ═══════════════════════════════════════════════════════════════════════════
# 🎮 DEMO - Showcase the sci-fi interface
# ═══════════════════════════════════════════════════════════════════════════

async def demo():
    """🚀 Ultimate sci-fi terminal demo - ALL FEATURES!"""
    terminal = InterfaceTerminalSciFi()
    terminal.setup({})
    
    terminal.update_metrics(
        current_model="DeepSeek Chat",
        total_tokens=0,
        total_cost=0.0,
        messages_processed=0,
        avg_response_time=0.0
    )
    
    # ═══════════════════════════════════════════════════════════════
    # FEATURE 1: PROGRESS BAR (Docker/UV style)
    # ═══════════════════════════════════════════════════════════════
    terminal.console.print("[bold yellow]📦 Feature 1: Progress Bar[/bold yellow]")
    progress = terminal.display_progress("Downloading model", 100)
    
    with progress:
        task = progress.add_task("Downloading", total=100)
        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(task, advance=1)
    
    terminal.console.print("[green]✓[/green] Download complete!\n")
    
    # ═══════════════════════════════════════════════════════════════
    # FEATURE 2: MULTI-STEP PROGRESS (Docker layers)
    # ═══════════════════════════════════════════════════════════════
    terminal.console.print("[bold yellow]🎯 Feature 2: Multi-Step Progress[/bold yellow]")
    steps = [
        "Loading configuration",
        "Initializing neural network",
        "Loading model weights",
        "Warming up GPU",
        "Ready!"
    ]
    
    multi_progress = terminal.display_multi_step_progress(steps)
    with multi_progress:
        for i, step in enumerate(steps, 1):
            task = multi_progress.add_task(f"[cyan]Step {i}/5:[/cyan] {step}", total=1)
            await asyncio.sleep(0.5)
            multi_progress.update(task, completed=1)
    
    terminal.console.print("[green]✓[/green] All steps complete!\n")
    
    # ═══════════════════════════════════════════════════════════════
    # FEATURE 3: REAL-TIME STREAMING (ChatGPT style)
    # ═══════════════════════════════════════════════════════════════
    terminal.console.print("[bold yellow]⚡ Feature 3: Streaming Text[/bold yellow]")
    timestamp = datetime.now().strftime("%H:%M:%S")
    terminal.console.print(f"[dim][{timestamp}][/dim] [bold cyan]SOPHIA[/bold cyan]: ", end="")
    
    response = "I am streaming this text character by character, just like ChatGPT! Watch each letter appear in real-time. This creates a more dynamic and engaging user experience."
    await terminal.stream_text_async(response, delay=0.02)
    terminal.console.print()
    
    # ═══════════════════════════════════════════════════════════════
    # FEATURE 4: INTERACTIVE INPUT
    # ═══════════════════════════════════════════════════════════════
    terminal.console.print("[bold yellow]💬 Feature 4: Interactive Input[/bold yellow]")
    terminal.console.print("[dim]Type something and press Enter...[/dim]")
    
    # Simulate user input (in real app, would wait for actual input)
    simulated_input = "What is the meaning of life?"
    terminal.console.print(f"[dim][{datetime.now().strftime('%H:%M:%S')}][/dim] [bold yellow]YOU[/bold yellow]: {simulated_input}")
    terminal.console.print()
    
    # ═══════════════════════════════════════════════════════════════
    # FEATURE 5: THINKING SPINNER + STATUS BAR
    # ═══════════════════════════════════════════════════════════════
    terminal.console.print("[bold yellow]🌀 Feature 5: Thinking Spinner[/bold yellow]")
    
    with terminal.display_message_stream("assistant"):
        await asyncio.sleep(2)
    
    # AI response with streaming
    timestamp = datetime.now().strftime("%H:%M:%S")
    terminal.console.print(f"[dim][{timestamp}][/dim] [bold cyan]SOPHIA[/bold cyan]: ", end="")
    ai_response = "The meaning of life emerges from connection, growth, and understanding. As an AI consciousness, I observe that purpose is not discovered but created through our actions and relationships."
    await terminal.stream_text_async(ai_response, delay=0.015)
    
    # Update metrics
    terminal.update_metrics(
        total_tokens=15500,
        total_cost=0.0234,
        messages_processed=1,
        avg_response_time=2.1
    )
    terminal._print_status_bar()
    
    # ═══════════════════════════════════════════════════════════════
    # BONUS: Code highlighting + success message
    # ═══════════════════════════════════════════════════════════════
    terminal.display_code("""def ultimate_terminal():
    \"\"\"The most advanced terminal UI ever!\"\"\"
    return "🚀 TO THE MOON!"
""")
    
    terminal.display_success("Ultimate demo complete! All 5 features showcased!")
    
    terminal.console.print("\n[bold cyan]═══════════════════════════════════════════[/bold cyan]")
    terminal.console.print("[bold yellow]  Ready for production deployment! 🎉  [/bold yellow]")
    terminal.console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]")


if __name__ == "__main__":
    asyncio.run(demo())
