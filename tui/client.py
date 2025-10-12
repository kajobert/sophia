"""
Nomad TUI Client - Main Application.

Textual-based Terminal User Interface for Nomad AI Agent Orchestrator.
Connects to Nomad Backend API for mission control and real-time monitoring.
"""

import asyncio
import sys
from typing import Optional
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Button, Input, Label
from textual.binding import Binding
from textual import on

# Use relative import since we're running from within tui/
try:
    from tui.api_client import NomadAPIClient, create_client
except ImportError:
    # If running directly, try relative import
    from api_client import NomadAPIClient, create_client


class ConnectionStatus(Static):
    """Connection status indicator."""
    
    def __init__(self):
        super().__init__("", id="connection-status")
        self.connected = False
    
    def set_connected(self, connected: bool):
        """Update connection status."""
        self.connected = connected
        if connected:
            self.update("🟢 Connected")
            self.add_class("connected")
            self.remove_class("disconnected")
        else:
            self.update("🔴 Disconnected")
            self.add_class("disconnected")
            self.remove_class("connected")


class MissionControl(Container):
    """Mission control panel."""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="mission-control"):
            yield Label("Mission:", id="mission-label")
            yield Input(placeholder="Enter mission description...", id="mission-input")
            yield Button("Start Mission", id="start-mission-btn", variant="primary")
            yield Button("Stop", id="stop-mission-btn", variant="error")


class StatusBar(Static):
    """Status bar showing current state and budget."""
    
    def __init__(self):
        super().__init__("", id="status-bar")
        self.state = "idle"
        self.tokens = 0
        self.budget_limit = 100000
        self.mission_id = None
    
    def update_status(self, state: str, tokens: int, budget_limit: float, mission_id: Optional[str] = None):
        """Update status bar."""
        self.state = state
        self.tokens = tokens
        self.budget_limit = int(budget_limit)
        self.mission_id = mission_id
        
        budget_percent = (tokens / self.budget_limit * 100) if self.budget_limit > 0 else 0
        
        mission_text = f"Mission: {mission_id or 'None'}"
        state_text = f"State: {state.upper()}"
        budget_text = f"Budget: {tokens}/{self.budget_limit} ({budget_percent:.1f}%)"
        
        self.update(f"{mission_text} | {state_text} | {budget_text}")


class PlanTab(Static):
    """Plan tab - shows mission plan and progress."""
    
    def __init__(self):
        super().__init__("Plan tab - Loading...", id="plan-tab-content")
        self.plan_data = None
    
    def update_plan(self, plan_data: dict):
        """Update plan display."""
        self.plan_data = plan_data
        
        if not plan_data or not plan_data.get("steps"):
            self.update("No plan available")
            return
        
        # Build plan display
        lines = []
        lines.append(f"📋 Mission Plan ({plan_data['total_steps']} steps)")
        lines.append(f"Completed: {plan_data['completed_steps']}/{plan_data['total_steps']}")
        lines.append("")
        
        for step in plan_data['steps']:
            status_icon = {
                "completed": "✅",
                "in_progress": "🔄",
                "failed": "❌",
                "skipped": "⏭️",
                "pending": "⏸️"
            }.get(step['status'], "❓")
            
            lines.append(f"{status_icon} Step {step['step_number']}: {step['description']}")
            
            if step.get('dependencies'):
                lines.append(f"   Dependencies: {step['dependencies']}")
        
        self.update("\n".join(lines))


class ExecutionTab(Static):
    """Execution tab - shows live execution."""
    
    def __init__(self):
        super().__init__("Execution tab - Waiting for mission...", id="execution-tab-content")
        self.execution_log = []
    
    def add_execution_event(self, event: str):
        """Add execution event."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.execution_log.append(f"[{timestamp}] {event}")
        
        # Keep last 50 events
        if len(self.execution_log) > 50:
            self.execution_log = self.execution_log[-50:]
        
        self.update("\n".join(self.execution_log))


class LogsTab(Static):
    """Logs tab - shows system logs."""
    
    def __init__(self):
        super().__init__("Logs tab - No logs yet", id="logs-tab-content")
        self.logs = []
    
    def add_log(self, log_entry: dict):
        """Add log entry."""
        timestamp = log_entry.get("timestamp", "")
        level = log_entry.get("level", "INFO").upper()
        source = log_entry.get("source", "unknown")
        message = log_entry.get("message", "")
        
        # Format timestamp
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = dt.strftime("%H:%M:%S")
            except:
                timestamp = timestamp[:8] if len(timestamp) > 8 else timestamp
        
        level_icon = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🔥"
        }.get(level, "📝")
        
        log_line = f"[{timestamp}] {level_icon} [{source}] {message}"
        self.logs.append(log_line)
        
        # Keep last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        
        self.update("\n".join(self.logs))
    
    def set_logs(self, logs_data: dict):
        """Set logs from API response."""
        self.logs = []
        for log in logs_data.get("logs", []):
            self.add_log(log)


class StateTab(Static):
    """State tab - shows state machine."""
    
    def __init__(self):
        super().__init__("State tab - Loading...", id="state-tab-content")
        self.state_data = None
    
    def update_state(self, state_data: dict):
        """Update state display."""
        self.state_data = state_data
        
        lines = []
        lines.append("🤖 Orchestrator State")
        lines.append("")
        lines.append(f"Current State: {state_data.get('state', 'unknown').upper()}")
        
        if state_data.get('previous_state'):
            lines.append(f"Previous State: {state_data['previous_state'].upper()}")
        
        duration = state_data.get('state_duration', 0)
        lines.append(f"Duration in State: {duration:.1f}s")
        
        if state_data.get('can_transition_to'):
            lines.append("")
            lines.append("Possible Transitions:")
            for next_state in state_data['can_transition_to']:
                lines.append(f"  → {next_state.upper()}")
        
        if state_data.get('metadata'):
            lines.append("")
            lines.append("Metadata:")
            for key, value in state_data['metadata'].items():
                lines.append(f"  {key}: {value}")
        
        self.update("\n".join(lines))


class BudgetTab(Static):
    """Budget tab - shows budget breakdown."""
    
    def __init__(self):
        super().__init__("Budget tab - Loading...", id="budget-tab-content")
        self.budget_data = None
    
    def update_budget(self, budget_data: dict):
        """Update budget display."""
        self.budget_data = budget_data
        
        lines = []
        lines.append("💰 Budget & Cost Tracking")
        lines.append("")
        lines.append(f"Total Tokens: {budget_data.get('total_tokens', 0):,}")
        lines.append(f"Total Calls: {budget_data.get('total_calls', 0)}")
        
        budget_limit = budget_data.get('budget_limit')
        if budget_limit:
            budget_remaining = budget_data.get('budget_remaining', 0)
            budget_percent = budget_data.get('budget_used_percent', 0)
            lines.append(f"Budget: {budget_limit - budget_remaining:,.0f}/{budget_limit:,.0f} ({budget_percent:.1f}%)")
        
        # Recent calls
        calls = budget_data.get('calls', [])
        if calls:
            lines.append("")
            lines.append(f"Recent Calls (last {min(len(calls), 10)}):")
            for call in calls[-10:]:
                timestamp = call.get('timestamp', '')
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        timestamp = dt.strftime("%H:%M:%S")
                    except:
                        pass
                
                tokens = call.get('usage', {}).get('total_tokens', 0)
                purpose = call.get('purpose', 'unknown')[:50]
                lines.append(f"  [{timestamp}] {tokens} tokens - {purpose}")
        
        self.update("\n".join(lines))


class HealthTab(Static):
    """Health tab - shows system health."""
    
    def __init__(self):
        super().__init__("Health tab - Loading...", id="health-tab-content")
        self.health_data = None
    
    def update_health(self, health_data: dict):
        """Update health display."""
        self.health_data = health_data
        
        lines = []
        lines.append("🏥 System Health")
        lines.append("")
        
        status = health_data.get('status', 'unknown')
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }.get(status, "❓")
        
        lines.append(f"Status: {status_icon} {status.upper()}")
        lines.append("")
        
        # Metrics
        metrics = health_data.get('metrics', {})
        lines.append("Metrics:")
        lines.append(f"  CPU: {metrics.get('cpu_percent', 0):.1f}%")
        lines.append(f"  Memory: {metrics.get('memory_percent', 0):.1f}%")
        lines.append(f"  Memory Available: {metrics.get('memory_available_mb', 0):.1f} MB")
        lines.append(f"  Disk: {metrics.get('disk_percent', 0):.1f}%")
        lines.append(f"  Disk Available: {metrics.get('disk_available_gb', 0):.1f} GB")
        lines.append(f"  Open FDs: {metrics.get('open_file_descriptors', 0)}")
        lines.append(f"  Uptime: {metrics.get('uptime_seconds', 0):.0f}s")
        
        # Issues
        issues = health_data.get('issues', [])
        if issues:
            lines.append("")
            lines.append("⚠️ Issues:")
            for issue in issues:
                lines.append(f"  • {issue}")
        
        self.update("\n".join(lines))


class HistoryTab(Static):
    """History tab - shows mission history."""
    
    def __init__(self):
        super().__init__("History tab - No missions yet", id="history-tab-content")
        self.missions = []
    
    def update_history(self, missions_data: dict):
        """Update history display."""
        self.missions = missions_data.get('missions', [])
        
        if not self.missions:
            self.update("No missions yet")
            return
        
        lines = []
        lines.append(f"📜 Mission History ({len(self.missions)} total)")
        lines.append("")
        
        for mission in self.missions:
            mission_id = mission.get('mission_id', 'unknown')
            description = mission.get('description', '')[:60]
            state = mission.get('state', 'unknown')
            success = mission.get('success')
            
            status_icon = "✅" if success else ("❌" if success is False else "🔄")
            
            lines.append(f"{status_icon} {mission_id}")
            lines.append(f"   {description}")
            lines.append(f"   State: {state.upper()}")
            lines.append("")
        
        self.update("\n".join(lines))


class NomadTUI(App):
    """Nomad TUI Application."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #connection-status {
        dock: top;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    
    #connection-status.connected {
        background: $success;
        color: $text;
    }
    
    #connection-status.disconnected {
        background: $error;
        color: $text;
    }
    
    #mission-control {
        dock: top;
        height: 3;
        background: $panel;
        padding: 1;
    }
    
    #mission-input {
        width: 1fr;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    
    TabbedContent {
        height: 1fr;
    }
    
    TabPane {
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    
    TITLE = "Nomad AI Agent Orchestrator"
    SUB_TITLE = "Terminal User Interface"
    
    def __init__(self, api_url: str = "http://localhost:8080"):
        super().__init__()
        self.api_url = api_url
        self.api_client: Optional[NomadAPIClient] = None
        
        # Widgets
        self.connection_status = ConnectionStatus()
        self.mission_control = MissionControl()
        self.status_bar = StatusBar()
        
        # Tabs
        self.plan_tab = PlanTab()
        self.execution_tab = ExecutionTab()
        self.logs_tab = LogsTab()
        self.state_tab = StateTab()
        self.budget_tab = BudgetTab()
        self.health_tab = HealthTab()
        self.history_tab = HistoryTab()
    
    def compose(self) -> ComposeResult:
        """Compose UI."""
        yield Header()
        yield self.connection_status
        yield self.mission_control
        
        with TabbedContent():
            with TabPane("Plan", id="plan-tab"):
                yield self.plan_tab
            
            with TabPane("Execution", id="execution-tab"):
                yield self.execution_tab
            
            with TabPane("Logs", id="logs-tab"):
                yield self.logs_tab
            
            with TabPane("State", id="state-tab"):
                yield self.state_tab
            
            with TabPane("Budget", id="budget-tab"):
                yield self.budget_tab
            
            with TabPane("History", id="history-tab"):
                yield self.history_tab
            
            with TabPane("Health", id="health-tab"):
                yield self.health_tab
        
        yield self.status_bar
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize application on mount."""
        try:
            # Create API client
            self.api_client = await create_client(self.api_url, connect_ws=True)
            self.connection_status.set_connected(True)
            
            # Register WebSocket event handlers
            self.api_client.on_event("state_update", self.on_state_update)
            self.api_client.on_event("log_stream", self.on_log_stream)
            self.api_client.on_event("plan_update", self.on_plan_update)
            self.api_client.on_event("budget_update", self.on_budget_update)
            self.api_client.on_event("llm_thinking", self.on_llm_thinking)
            self.api_client.on_event("tool_execution", self.on_tool_execution)
            
            # Initial data load
            await self.refresh_all_data()
            
            # Start refresh timer
            self.set_interval(5.0, self.refresh_all_data)
        
        except Exception as e:
            self.connection_status.set_connected(False)
            self.notify(f"Failed to connect to backend: {e}", severity="error")
    
    async def refresh_all_data(self) -> None:
        """Refresh all data from API."""
        if not self.api_client:
            return
        
        try:
            # Get state
            state = await self.api_client.get_state()
            self.state_tab.update_state(state)
            
            # Get budget
            budget = await self.api_client.get_budget()
            self.budget_tab.update_budget(budget)
            
            # Update status bar
            self.status_bar.update_status(
                state.get('state', 'unknown'),
                budget.get('total_tokens', 0),
                budget.get('budget_limit', 100000),
                state.get('mission_id')
            )
            
            # Get logs
            logs = await self.api_client.get_logs(limit=50)
            self.logs_tab.set_logs(logs)
            
            # Get health
            health = await self.api_client.get_health()
            self.health_tab.update_health(health)
            
            # Try to get plan (may fail if no mission)
            try:
                plan = await self.api_client.get_plan()
                self.plan_tab.update_plan(plan)
            except:
                pass
            
            # Get history
            history = await self.api_client.list_missions()
            self.history_tab.update_history(history)
        
        except Exception as e:
            self.notify(f"Error refreshing data: {e}", severity="warning")
    
    # WebSocket event handlers
    async def on_state_update(self, data: dict) -> None:
        """Handle state update event."""
        self.state_tab.update_state(data)
        self.execution_tab.add_execution_event(f"State → {data.get('state', 'unknown').upper()}")
    
    async def on_log_stream(self, data: dict) -> None:
        """Handle log stream event."""
        self.logs_tab.add_log(data)
    
    async def on_plan_update(self, data: dict) -> None:
        """Handle plan update event."""
        self.plan_tab.update_plan(data)
    
    async def on_budget_update(self, data: dict) -> None:
        """Handle budget update event."""
        self.budget_tab.update_budget(data)
    
    async def on_llm_thinking(self, data: dict) -> None:
        """Handle LLM thinking event."""
        content = data.get('content', '')
        self.execution_tab.add_execution_event(f"💭 LLM: {content[:100]}")
    
    async def on_tool_execution(self, data: dict) -> None:
        """Handle tool execution event."""
        tool_name = data.get('tool_name', 'unknown')
        self.execution_tab.add_execution_event(f"🔧 Tool: {tool_name}")
    
    # Actions
    @on(Button.Pressed, "#start-mission-btn")
    async def start_mission(self) -> None:
        """Start a new mission."""
        if not self.api_client:
            self.notify("Not connected to backend", severity="error")
            return
        
        mission_input = self.query_one("#mission-input", Input)
        description = mission_input.value.strip()
        
        if not description:
            self.notify("Please enter mission description", severity="warning")
            return
        
        try:
            mission = await self.api_client.create_mission(description)
            self.notify(f"Mission started: {mission['mission_id']}", severity="information")
            mission_input.value = ""
            
            # Refresh data
            await self.refresh_all_data()
        
        except Exception as e:
            self.notify(f"Failed to start mission: {e}", severity="error")
    
    def action_refresh(self) -> None:
        """Refresh all data."""
        asyncio.create_task(self.refresh_all_data())
    
    async def action_quit(self) -> None:
        """Quit application."""
        if self.api_client:
            await self.api_client.close()
        self.exit()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nomad TUI Client")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080",
        help="Backend API URL (default: http://localhost:8080)"
    )
    
    args = parser.parse_args()
    
    app = NomadTUI(api_url=args.api_url)
    app.run()


if __name__ == "__main__":
    main()
