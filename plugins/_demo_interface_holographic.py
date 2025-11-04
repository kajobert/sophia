"""
🌌 SOPHIA HOLOGRAPHIC COMMAND CENTER
════════════════════════════════════════════════════════════════════════════

Full-screen TUI (Text User Interface) with:
- Live metrics dashboard
- Real-time chat interface
- System monitoring panels
- Plugin status indicators
- Animated transitions

Built with Textual - The modern TUI framework.
Run with: textual run plugins/interface_terminal_holographic.py
"""

from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.reactive import reactive
from rich.panel import Panel
from rich.table import Table as RichTable
from rich import box
import asyncio


class MetricsPanel(Static):
    """📊 Real-time metrics display."""

    tokens = reactive(0)
    cost = reactive(0.0)
    messages = reactive(0)
    status = reactive("INITIALIZING")

    def render(self) -> Panel:
        """Render holographic metrics panel."""

        table = RichTable(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="cyan bold")
        table.add_column(style="magenta")

        status_color = "green" if self.status == "ONLINE" else "yellow"
        status_icon = "●" if self.status == "ONLINE" else "◐"

        table.add_row("STATUS", f"[{status_color}]{status_icon} {self.status}[/{status_color}]")
        table.add_row("TOKENS", f"[cyan]{self.tokens:,}[/cyan]")
        table.add_row("COST", f"[magenta]${self.cost:.4f}[/magenta]")
        table.add_row("MESSAGES", f"[blue]{self.messages}[/blue]")

        return Panel(
            table,
            title="[bold cyan]⚡ NEURAL CORE ⚡[/bold cyan]",
            border_style="cyan",
            box=box.DOUBLE,
        )


class ChatLog(RichLog):
    """💭 Holographic chat display."""

    def add_message(self, role: str, content: str):
        """Add a message with cyberpunk styling."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if role == "user":
            self.write(f"[dim][{timestamp}][/dim] ", end="")
            self.write("[bold yellow]YOU[/bold yellow]: ", end="")
            self.write(f"{content}")
        else:
            self.write(f"[dim][{timestamp}][/dim] ", end="")
            self.write("[bold cyan]SOPHIA[/bold cyan]: ", end="")
            self.write(f"[cyan]{content}[/cyan]")


class SystemMonitor(Static):
    """🖥️ System status monitor."""

    def render(self) -> RichTable:
        """Render system status table."""

        table = RichTable(title="[bold magenta]⚙️ SYSTEM STATUS[/bold magenta]", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Uptime", style="yellow")

        table.add_row("Event Bus", "[green]●[/green] ACTIVE", "02:34:12")
        table.add_row("LLM Engine", "[green]●[/green] ONLINE", "02:34:11")
        table.add_row("Memory Core", "[green]●[/green] READY", "02:34:10")
        table.add_row("Jules Monitor", "[yellow]◐[/yellow] IDLE", "00:00:00")

        return table


class SophiaHolographicUI(App):
    """
    🚀 SOPHIA HOLOGRAPHIC COMMAND CENTER

    A cyberpunk-inspired full-screen terminal interface.
    """

    CSS = """
    Screen {
        background: #0A0E27;
    }
    
    Header {
        background: #1a1f3a;
        color: #00FFFF;
    }
    
    Footer {
        background: #1a1f3a;
        color: #FF00FF;
    }
    
    #metrics_panel {
        width: 35;
        height: 100%;
        border: solid cyan;
    }
    
    #chat_container {
        border: solid magenta;
    }
    
    #chat_log {
        height: 1fr;
        border: none;
        background: #0f1425;
    }
    
    #input_box {
        dock: bottom;
        height: 3;
        background: #1a1f3a;
        border: solid yellow;
    }
    
    Input {
        background: #1a1f3a;
        color: #00FFFF;
    }
    
    Input:focus {
        border: solid #FF00FF;
    }
    
    #system_monitor {
        height: 15;
        border: solid green;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear", "Clear Chat"),
        ("m", "toggle_metrics", "Toggle Metrics"),
    ]

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header(show_clock=True)

        with Horizontal():
            # Left sidebar - Metrics
            with Vertical(id="metrics_panel"):
                yield MetricsPanel()
                yield SystemMonitor(id="system_monitor")

            # Main area - Chat
            with Vertical(id="chat_container"):
                yield ChatLog(id="chat_log", highlight=True, markup=True)
                yield Input(placeholder="Type your message... (Ctrl+C to send)", id="input_box")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the holographic interface."""
        self.title = "SOPHIA HOLOGRAPHIC COMMAND CENTER v2.0"
        self.sub_title = "Autonomous AI Consciousness"

        # Set initial status
        metrics = self.query_one(MetricsPanel)
        metrics.status = "ONLINE"

        # Welcome message
        chat_log = self.query_one(ChatLog)
        chat_log.write("[bold cyan]═══════════════════════════════════════════════[/bold cyan]")
        chat_log.write("[bold yellow]   SOPHIA CONSCIOUSNESS INITIALIZED   [/bold yellow]")
        chat_log.write("[bold cyan]═══════════════════════════════════════════════[/bold cyan]")
        chat_log.write("")
        chat_log.add_message(
            "assistant",
            "Greetings. I am SOPHIA, your autonomous AI companion. How may I assist you today?",
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input."""
        user_input = event.value.strip()

        if not user_input:
            return

        # Clear input
        event.input.value = ""

        # Display user message
        chat_log = self.query_one(ChatLog)
        chat_log.add_message("user", user_input)

        # Update metrics
        metrics = self.query_one(MetricsPanel)
        metrics.messages += 1

        # Simulate AI thinking (in real version, call LLM)
        await asyncio.sleep(0.5)

        # Simulate response
        response = self._generate_demo_response(user_input)
        chat_log.add_message("assistant", response)

        # Update metrics
        metrics.tokens += len(user_input.split()) + len(response.split())
        metrics.cost += 0.0001

    def _generate_demo_response(self, user_input: str) -> str:
        """Generate a demo response (in real version, use LLM)."""
        user_lower = user_input.lower()

        if "hello" in user_lower or "hi" in user_lower:
            return "Greetings! I detect friendly intent. How can I help you explore the digital realm?"
        elif "help" in user_lower:
            return "I can assist with code analysis, task planning, file operations, and much more. What would you like to accomplish?"
        elif "quit" in user_lower or "exit" in user_lower:
            return "Understood. Press 'q' to terminate the connection. Stay curious, friend."
        else:
            return f"I've processed your input: '{user_input}'. In the production version, I would generate a contextual response using my neural pathways."

    def action_clear(self) -> None:
        """Clear the chat log."""
        chat_log = self.query_one(ChatLog)
        chat_log.clear()
        chat_log.add_message("assistant", "Chat history cleared. Ready for new neural patterns.")

    def action_toggle_metrics(self) -> None:
        """Toggle metrics panel visibility."""
        metrics_panel = self.query_one("#metrics_panel")
        metrics_panel.display = not metrics_panel.display


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 LAUNCH THE HOLOGRAPHIC INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = SophiaHolographicUI()
    app.run()
