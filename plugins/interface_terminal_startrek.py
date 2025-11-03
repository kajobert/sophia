#!/usr/bin/env python3
"""
SOPHIA - Star Trek Terminal Interface
======================================
"Space... the final frontier" 🖖

LCARS AESTHETIC - Pro Radka
Inspired by: Star Trek: The Next Generation (1987-1994)
Theme: LCARS interface, orange/blue colors, starship console
"""

import asyncio
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich import box

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from plugins.base_plugin import BasePlugin


class InterfaceTerminalStarTrek(BasePlugin):
    """
    STAR TREK LCARS TERMINAL INTERFACE
    
    ╔════════════════════════════════════════════╗
    ║  USS SOPHIA NCC-1701-AI                   ║
    ║  LCARS v24.3 - MAIN COMPUTER              ║
    ║  STARDATE: 2025.11.03                     ║
    ╚════════════════════════════════════════════╝
    
    Features:
    - LCARS color scheme (orange, blue, purple)
    - Starship computer aesthetic
    - "Computer working..." animations
    - Stardate timestamps
    - Federation standard interface
    """
    
    @property
    def name(self) -> str:
        return "interface_terminal_startrek"
    
    @property
    def plugin_type(self) -> str:
        return "interface"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.plugin_name = "interface_terminal_startrek"
        self.console = Console()
        
        # LCARS color palette
        self.colors = {
            'primary': '#FF9900',      # LCARS Orange
            'secondary': '#9999FF',    # LCARS Purple
            'tertiary': '#CC6699',     # LCARS Pink
            'accent': '#FFCC66',       # LCARS Light Orange
            'blue': '#6699CC',         # LCARS Blue
            'highlight': '#FF9900',    # Orange highlight
            'dim': '#CC6600',          # Dark orange
            'success': '#99CC99',      # LCARS Green
            'warning': '#FFCC00',      # Yellow
            'error': '#CC3333',        # LCARS Red
        }
        
        # Metrics
        self.message_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.response_times = []
        self.current_model = "M-5 Multitronic Unit"
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Initialize Star Trek LCARS interface."""
        self.console.clear()
        self._display_lcars_boot()
    
    def _display_lcars_boot(self):
        """Display LCARS-style boot sequence - simple text, no boxes!"""
        self.console.print()
        self.console.print("[bold bright_yellow]USS SOPHIA NCC-1701-AI[/]")
        self.console.print("[yellow]LCARS v24.3 - MAIN COMPUTER[/]")
        self.console.print("[dim yellow]STARDATE: 2025.11.03[/]")
        self.console.print()
        self.console.print("[bright_blue]▸[/] [blue]COMPUTER ONLINE[/]")
        self.console.print("[bright_blue]▸[/] [blue]AI CORE INITIALIZED[/]")
        self.console.print("[bright_blue]▸[/] [blue]ALL SYSTEMS NOMINAL[/]")
        self.console.print()
        self.console.print("[dim blue]'Make it so.' - Captain Picard[/]")
        self.console.print()
    
    def _get_stardate(self) -> str:
        """Calculate Star Trek style stardate."""
        now = datetime.now()
        # Simplified stardate: YYYY.MMDD.HHMM
        return f"{now.year}.{now.month:02d}{now.day:02d}.{now.hour:02d}{now.minute:02d}"
    
    def _print_status_bar(self):
        """Print LCARS-style status bar (single line)."""
        avg_time = sum(self.response_times[-10:]) / len(self.response_times[-10:]) if self.response_times else 0
        
        status = Text()
        status.append("●", style="bold yellow")
        status.append(" │ ", style="dim yellow")
        status.append(f"{self.current_model}", style="yellow")
        status.append(" │ ", style="dim yellow")
        status.append(f"{self.total_tokens:,}tok", style="bright_yellow")
        status.append(" │ ", style="dim yellow")
        status.append(f"${self.total_cost:.4f}", style="yellow")
        status.append(" │ ", style="dim yellow")
        status.append(f"{self.message_count}msg", style="bright_yellow")
        status.append(" │ ", style="dim yellow")
        status.append(f"{avg_time:.1f}s", style="yellow")
        
        self.console.print(status)
    
    def display_message(self, role: str, content: str, **kwargs):
        """Display message in LCARS style."""
        stardate = self._get_stardate()
        
        if role.upper() == "USER" or role.upper() == "YOU":
            prefix = f"[dim blue][SD {stardate}][/] [bold bright_yellow]CREW:[/]"
        elif role.upper() in ["SOPHIA", "ASSISTANT", "AI"]:
            prefix = f"[dim blue][SD {stardate}][/] [bold yellow]COMPUTER:[/]"
        elif role.upper() == "SYSTEM":
            prefix = f"[dim blue][SD {stardate}][/] [blue]SYSTEM:[/]"
        else:
            prefix = f"[dim blue][SD {stardate}][/] [yellow]{role.upper()}:[/]"
        
        self.console.print(f"{prefix} [bright_yellow]{content}[/]")
    
    def display_message_stream(self, role: str, content_generator, **kwargs):
        """Display streaming message with LCARS computer working animation."""
        stardate = self._get_stardate()
        
        if role.upper() in ["SOPHIA", "ASSISTANT", "AI"]:
            prefix = f"[dim blue][SD {stardate}][/] [bold yellow]COMPUTER:[/]"
        else:
            prefix = f"[dim blue][SD {stardate}][/] [yellow]{role.upper()}:[/]"
        
        # "Computer working" spinner
        with self.console.status(f"[bold blue]◉[/] [yellow]COMPUTER:[/] [dim blue]processing...[/]", spinner="dots") as status:
            time.sleep(2)
        
        # Stream the response
        self.console.print(prefix, end=" ")
        
        full_response = ""
        for chunk in content_generator:
            self.console.print(f"[bright_yellow]{chunk}[/]", end="")
            full_response += chunk
            time.sleep(0.03)
        
        self.console.print()
        
        # Update metrics
        self.message_count += 1
        self.total_tokens += kwargs.get('tokens', 500)
        self.total_cost += kwargs.get('cost', 0.001)
        self.response_times.append(kwargs.get('response_time', 2.0))
        
        # Status bar
        self._print_status_bar()
    
    def display_code(self, code: str, language: str = "python", title: str = "CODE"):
        """Display code with LCARS styling."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        
        panel = Panel(
            syntax,
            title=f"[bold yellow]▸ {title} ◂[/]",
            border_style="yellow",
            box=box.MINIMAL,
            padding=(0, 1)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def display_progress(self) -> Progress:
        """Return LCARS-style progress bar."""
        return Progress(
            SpinnerColumn(spinner_name="dots", style="bold blue"),
            TextColumn("[yellow]{task.description}[/]"),
            BarColumn(bar_width=None, style="yellow", complete_style="bright_yellow"),
            TextColumn("[bright_yellow]{task.completed}/{task.total}[/]"),
            TimeElapsedColumn(),
            console=self.console
        )
    
    def display_multi_step_progress(self) -> Progress:
        """Return LCARS-style multi-step progress."""
        return Progress(
            TextColumn("[dim blue]▸[/] [yellow]{task.description}[/]"),
            BarColumn(style="yellow", complete_style="bright_yellow"),
            TextColumn("[bright_yellow]{task.completed}/{task.total}[/]"),
            console=self.console
        )
    
    def stream_text(self, text: str, delay: float = 0.03):
        """Stream text character by character (synchronous)."""
        for char in text:
            self.console.print(f"[bright_yellow]{char}[/]", end="")
            time.sleep(delay)
        self.console.print()
    
    async def stream_text_async(self, text: str, delay: float = 0.03):
        """Stream text character by character (asynchronous)."""
        for char in text:
            self.console.print(f"[bright_yellow]{char}[/]", end="")
            await asyncio.sleep(delay)
        self.console.print()
    
    def get_user_input(self, prompt: str = "Enter command") -> str:
        """Get user input with LCARS styling and blinking cursor."""
        stardate = self._get_stardate()
        
        try:
            user_input = Prompt.ask(f"[dim blue][SD {stardate}][/] [bold bright_yellow]CREW[/] [orange1]▌[/orange1]")
            return user_input
        except:
            return input(f"[SD {stardate}] CREW ▌ ")
    
    def display_error(self, message: str):
        """Display error in LCARS style."""
        self.console.print(f"\n[bold red]⚠[/] [red]ALERT: {message}[/]\n")
    
    def display_success(self, message: str):
        """Display success message."""
        self.console.print(f"\n[bold green]✓[/] [green]{message}[/]\n")
    
    def display_alert(self, message: str, level: str = "warning"):
        """Display LCARS alert."""
        if level == "red":
            color = "red"
            icon = "⚠⚠⚠"
        elif level == "yellow":
            color = "yellow"
            icon = "⚠"
        else:
            color = "blue"
            icon = "ℹ"
        
        self.console.print(f"\n[bold {color}]{icon} {message.upper()} {icon}[/]\n")
    
    async def execute(self, **kwargs):
        """Plugin execution (not used for interface)."""
        return {"status": "lcars_interface_active"}


async def demo():
    """Demo všech Star Trek LCARS features."""
    interface = InterfaceTerminalStarTrek()
    interface.setup({})
    
    print("\n")
    interface.console.print("[bold yellow]═" * 35 + "[/]")
    interface.console.print("[bold bright_yellow]  LCARS TERMINAL - Feature Demo  [/]")
    interface.console.print("[bold yellow]═" * 35 + "[/]")
    print("\n")
    
    # Feature 1: Progress Bar
    interface.console.print("[bold bright_yellow]📥 Feature 1: Warp Core Initialization[/]\n")
    
    with interface.display_progress() as progress:
        task = progress.add_task("[yellow]Charging dilithium crystals...", total=100)
        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(task, advance=1)
    
    interface.display_success("Warp core online!")
    
    # Feature 2: Multi-Step Progress
    interface.console.print("\n[bold bright_yellow]🎯 Feature 2: System Diagnostics[/]\n")
    
    steps = [
        ("Main power online", 1),
        ("Shields at maximum", 1),
        ("Weapons systems armed", 1),
        ("Life support nominal", 1),
        ("All systems ready", 1),
    ]
    
    with interface.display_multi_step_progress() as progress:
        for i, (desc, total) in enumerate(steps, 1):
            task = progress.add_task(f"Step {i}/{len(steps)}: {desc}", total=total)
            await asyncio.sleep(0.5)
            progress.update(task, advance=1)
    
    interface.display_success("USS Sophia ready for departure!")
    
    # Feature 3: Streaming Text
    interface.console.print("\n[bold bright_yellow]⚡ Feature 3: Computer Voice Synthesis[/]\n")
    
    interface.console.print("[dim blue][SD 2025.1103.2045][/] [bold yellow]PICARD:[/] ", end="")
    await interface.stream_text_async(
        "Engage! Set course for the future, maximum warp!",
        delay=0.02
    )
    
    # Feature 4: Interactive Input
    interface.console.print("\n[bold bright_yellow]💬 Feature 4: Bridge Command Input[/]\n")
    
    interface.console.print("[dim blue][SD 2025.1103.2046][/] [bold bright_yellow]CREW:[/] [bright_yellow]Computer, what is our current status?[/]")
    
    # Feature 5: Thinking Spinner + Status
    interface.console.print("\n[bold bright_yellow]🌀 Feature 5: Computer Processing + Status[/]\n")
    
    def response_gen():
        response = "All systems functioning within normal parameters. Ship is ready for your command, Captain."
        for char in response:
            yield char
    
    interface.current_model = "M-5 Multitronic Unit"
    interface.display_message_stream(
        "SOPHIA",
        response_gen(),
        tokens=1500,
        cost=0.0234,
        response_time=2.1
    )
    
    # Feature 6: Alert System
    interface.console.print("\n[bold bright_yellow]🚨 Feature 6: LCARS Alert System[/]\n")
    
    interface.display_alert("RED ALERT - INCOMING TRANSMISSION", level="red")
    await asyncio.sleep(1)
    interface.display_alert("Yellow Alert - Shields Raised", level="yellow")
    await asyncio.sleep(1)
    interface.display_alert("Information: Scan complete", level="info")
    
    # Final: Code Display
    interface.console.print("\n[bold bright_yellow]💻 Feature 7: LCARS Code Display[/]\n")
    
    code_sample = '''def engage_warp_drive(warp_factor: int):
    """Set warp speed - maximum warp 9.99"""
    if warp_factor > 9:
        print("Warning: Exceeding recommended speed")
    dilithium_crystals.activate()
    warp_core.set_speed(warp_factor)
    return f"Warp {warp_factor} - Engaged!"'''
    
    interface.display_code(code_sample, "python", "WARP_DRIVE.PY")
    
    interface.console.print("[bold yellow]═" * 35 + "[/]")
    interface.console.print("[bold bright_yellow]  ✓ LCARS Demo Complete!  [/]")
    interface.console.print("[dim blue]  'Make it so.' - Picard 🖖  [/]")
    interface.console.print("[bold yellow]═" * 35 + "[/]\n")


if __name__ == "__main__":
    asyncio.run(demo())
