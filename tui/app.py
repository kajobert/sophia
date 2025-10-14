import sys
import os
import asyncio
import traceback
from typing import Optional

# Add the project root to the path to allow importing from `core`
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, TabbedContent, TabPane, RichLog, Static, TextArea
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.table import Table

from core.orchestrator import NomadOrchestrator
from core.rich_printer import RichPrinter
from core.state_manager import State
from tui.widgets.status_widget import StatusWidget
from tui.widgets.memory_log_widget import MemoryLogWidget
from tui.widgets.statistics_widget import StatisticsWidget
from tui.messages import LogMessage, ChatMessage

CRASH_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "crash.log")

class SophiaTUI(App):
    """A modern TUI for interacting with the Nomad agent."""

    TITLE = "Nomad - AI Software Engineer"
    SUB_TITLE = "Architecture: Single Brain - State Machine"

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle Dark Mode"),
        ("ctrl+q", "request_quit", "Quit"),
        ("enter", "submit_prompt", "Submit Prompt"),
    ]

    def __init__(self, session_id: Optional[str] = None):
        super().__init__()
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.explanation_widget = Static(id="explanation", markup=True)
        self.current_explanation = ""
        self.tool_widget = RichLog(id="tool_output", highlight=True, markup=True)
        self.tool_widget.border_title = "Tool Output"

        self.system_log_widget = StatusWidget(id="system_log_view")
        self.system_log_widget.border_title = "System Logs"

        self.communication_log_widget = RichLog(id="communication_log_view", highlight=True, markup=True)
        self.communication_log_widget.border_title = "Communication Log"

        self.error_log_widget = RichLog(id="error_log_view", highlight=True, markup=True)
        self.error_log_widget.border_title = "Error Log"

        self.memory_log_widget = MemoryLogWidget(id="memory_log_view")
        self.statistics_widget = StatisticsWidget(id="statistics_view")

        self.orchestrator = NomadOrchestrator(
            project_root=self.project_root,
            session_id=session_id
        )
        self.input_widget = TextArea(theme="monokai")
        self.input_widget.border_title = "Your command (Enter to submit, Ctrl+Enter for new line)"

    def compose(self) -> ComposeResult:
        """Composes the TUI layout."""
        yield Header()
        with TabbedContent(initial="agent_tab"):
            with TabPane("Agent", id="agent_tab"):
                with VerticalScroll(id="explanation-container"):
                    yield self.explanation_widget
                yield self.tool_widget
            with TabPane("Communication", id="communication_tab"):
                yield self.communication_log_widget
            with TabPane("System Logs", id="system_log_tab"):
                yield self.system_log_widget
            with TabPane("Memory", id="memory_tab"):
                yield self.memory_log_widget
            with TabPane("Errors", id="error_log_tab"):
                yield self.error_log_widget
            with TabPane("Statistics", id="statistics_tab"):
                yield self.statistics_widget
        yield self.input_widget
        yield Footer()

    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        RichPrinter.set_message_poster(self.post_message)
        self.input_widget.focus()
        self.run_orchestrator(initial_prompt=None)
        self.set_interval(1, self.update_status_and_stats)

    def update_status_and_stats(self) -> None:
        """Periodically updates the status bar and statistics."""
        # Update status in the footer
        current_state = self.orchestrator.state_manager.current_state
        self.sub_title = f"Architecture: Single Brain | State: {current_state.value.upper()}"
        # Update statistics
        # total_cost = self.orchestrator.budget_tracker.get_total_cost() # TODO: Re-implement budget tracker
        total_cost = 0.0
        completed_tasks = 0 # TODO: Implement task tracking
        self.statistics_widget.set_statistics(total_cost, completed_tasks)

    @work(exclusive=True)
    async def run_orchestrator(self, initial_prompt: Optional[str]):
        """Runs the main orchestrator loop in a separate worker."""
        try:
            await self.orchestrator.run(initial_prompt)
        except Exception as e:
            RichPrinter.fatal(f"FATAL ORCHESTRATOR ERROR: {e}")
            self.app.exit()

    async def action_submit_prompt(self) -> None:
        """Handles the user submitting a prompt."""
        prompt = self.input_widget.text
        if not prompt:
            return

        user_panel = Panel(f"{prompt}", title="User", border_style="green")
        self.tool_widget.write(user_panel)
        self.input_widget.clear()

        self.current_explanation = ""
        self.explanation_widget.update("")

        current_state = self.orchestrator.state_manager.current_state
        if current_state == State.AWAITING_USER_INPUT:
            self.run_orchestrator(initial_prompt=prompt)
        else:
            RichPrinter.warn("The orchestrator is busy. Please wait for the current operation to complete.")

    def on_log_message(self, message: LogMessage) -> None:
        """Handles a log message and displays it in the System Logs tab."""
        self.system_log_widget.add_log(message.text, message.level)

    def on_chat_message(self, message: ChatMessage) -> None:
        """Handles a chat message and displays it in the appropriate widget."""
        msg_type = message.msg_type
        content = message.content

        def write_to_tool_widget(panel_content, title, border_style):
            self.tool_widget.write(Panel(panel_content, title=title, border_style=border_style))

        if msg_type == "explanation_chunk":
            self.current_explanation += content
            md_panel = Panel(Markdown(self.current_explanation), border_style="blue", title="Thought Process")
            self.explanation_widget.update(md_panel)
            self.query_one("#explanation-container", VerticalScroll).scroll_end(animate=False)
        elif msg_type == "tool_code":
            panel_content = Syntax(content, "json", theme="monokai", line_numbers=True)
            write_to_tool_widget(panel_content, "Tool Call", "yellow")
        elif msg_type == "tool_output":
            write_to_tool_widget(content, "Tool Output", "bright_cyan")
        elif msg_type == "inform":
            write_to_tool_widget(content, "Information", "bright_green")
        elif msg_type == "task_complete":
            write_to_tool_widget(content, "Task Complete", "bold green")
        elif msg_type == "error_log":
            self.error_log_widget.write(content)
        else:
            self.system_log_widget.add_log(f"Unknown message type '{msg_type}': {content}", "WARNING")

    async def action_request_quit(self):
        """Safely quits the application."""
        RichPrinter.info("Initiating shutdown...")
        await self.orchestrator.shutdown()
        self.exit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the Nomad TUI.")
    parser.add_argument("--session", help="Session ID to continue a previous session.")
    args = parser.parse_args()

    RichPrinter.configure_logging()

    try:
        app = SophiaTUI(session_id=args.session)
        app.run()
    except Exception as e:
        os.makedirs(os.path.dirname(CRASH_LOG_PATH), exist_ok=True)
        with open(CRASH_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("--- TUI APPLICATION CRASHED UNEXPECTEDLY ---\n\n")
            traceback.print_exc(file=f)

        print(f"\n[FATAL] TUI application crashed. See {CRASH_LOG_PATH} for details.", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)