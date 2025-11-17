"""Terminal dashboard for Sophia telemetry."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, Iterable, Optional

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

try:  # pragma: no cover - psutil is optional
	import psutil  # type: ignore
except Exception:  # noqa: BLE001
	psutil = None  # type: ignore


DEFAULT_SERVER = os.getenv("SOPHIA_SERVER", "http://localhost:8000")
HISTORY_LIMIT = 120


def format_duration(seconds: float) -> str:
	"""Convert seconds to a human-readable string."""

	seconds = max(int(seconds), 0)
	hours, remainder = divmod(seconds, 3600)
	minutes, secs = divmod(remainder, 60)
	if hours:
		return f"{hours}h {minutes}m"
	if minutes:
		return f"{minutes}m {secs}s"
	return f"{secs}s"


def format_tokens(value: float) -> str:
	"""Format token counts with thousands separators."""

	return f"{int(value):,}"


def project_monthly_spend(cost_so_far: float, uptime_seconds: float) -> float:
	"""Project 30-day spend based on cost so far and uptime."""

	if uptime_seconds <= 0:
		return cost_so_far
	hourly = cost_so_far / max(uptime_seconds / 3600, 1e-6)
	return hourly * 24 * 30


@dataclass(slots=True)
class UsageSummary:
	"""Normalized token and cost metrics from a telemetry snapshot."""

	prompt_tokens: int = 0
	completion_tokens: int = 0
	total_tokens: int = 0
	online_tokens: int = 0
	offline_tokens: int = 0
	hybrid_tokens: int = 0
	cost_usd: float = 0.0

	@staticmethod
	def _to_int(value: Any) -> int:
		try:
			return int(value)
		except (TypeError, ValueError):
			return 0

	@staticmethod
	def _to_float(value: Any) -> float:
		try:
			return float(value)
		except (TypeError, ValueError):
			return 0.0

	@classmethod
	def from_snapshot(cls, snapshot: Dict[str, Any]) -> "UsageSummary":
		"""Build a summary using all known token/cost fields."""

		prompt = cls._to_int(
			snapshot.get("total_tokens_prompt")
			or snapshot.get("prompt_tokens")
			or snapshot.get("tokens_prompt")
		)
		completion = cls._to_int(
			snapshot.get("total_tokens_completion")
			or snapshot.get("completion_tokens")
			or snapshot.get("tokens_completion")
		)
		reported_total = cls._to_int(snapshot.get("total_tokens") or snapshot.get("tokens"))
		mode_total = (
			cls._to_int(snapshot.get("online_tokens"))
			+ cls._to_int(snapshot.get("offline_tokens"))
			+ cls._to_int(snapshot.get("hybrid_tokens"))
		)
		total_tokens = reported_total or prompt + completion or mode_total
		total_tokens = max(total_tokens, prompt + completion, mode_total)
		cost_usd = cls._to_float(
			snapshot.get("total_cost_usd")
			or snapshot.get("total_cost")
			or snapshot.get("cost_usd")
		)
		return cls(
			prompt_tokens=prompt,
			completion_tokens=completion,
			total_tokens=total_tokens,
			online_tokens=cls._to_int(snapshot.get("online_tokens")),
			offline_tokens=cls._to_int(snapshot.get("offline_tokens")),
			hybrid_tokens=cls._to_int(snapshot.get("hybrid_tokens")),
			cost_usd=cost_usd,
		)


@dataclass(slots=True)
class DashboardState:
	"""Tracks telemetry snapshots and derived metrics for rendering."""

	snapshot: Optional[Dict[str, Any]] = None
	usage: Optional[UsageSummary] = None
	tokens_history: Deque[float] = field(
		default_factory=lambda: deque(maxlen=HISTORY_LIMIT)
	)
	cost_history: Deque[float] = field(default_factory=lambda: deque(maxlen=HISTORY_LIMIT))
	error_message: Optional[str] = None

	def update(self, snapshot: Dict[str, Any]) -> None:
		"""Store the latest snapshot and append history samples."""

		self.snapshot = snapshot
		self.usage = UsageSummary.from_snapshot(snapshot)
		self.tokens_history.append(float(self.usage.total_tokens))
		self.cost_history.append(float(self.usage.cost_usd))
		self.error_message = None

	def note_error(self, message: str) -> None:
		"""Record a transient error for footer display."""

		self.error_message = message


class TelemetryClient:
	"""Fetch telemetry snapshots from the Sophia Web UI server."""

	def __init__(self, base_url: str, timeout: float = 2.0) -> None:
		self.base_url = base_url.rstrip("/")
		self.timeout = timeout

	def fetch_snapshot(self) -> Optional[Dict[str, Any]]:
		"""Retrieve telemetry data from primary or fallback endpoints."""

		last_error: Optional[str] = None
		for endpoint in ("/api/telemetry", "/api/stats"):
			url = f"{self.base_url}{endpoint}"
			try:
				request = urllib.request.Request(
					url, headers={"User-Agent": "SophiaCLI/1.0"}
				)
				with urllib.request.urlopen(request, timeout=self.timeout) as response:
					payload = json.load(response)

				if endpoint.endswith("telemetry"):
					return payload

				telemetry_payload = payload.get("telemetry") if isinstance(payload, dict) else None
				if isinstance(telemetry_payload, dict):
					return telemetry_payload
			except urllib.error.URLError as exc:  # pragma: no cover - network dependent
				reason = exc.reason if hasattr(exc, "reason") else exc
				last_error = f"{url}: {reason}"
			except Exception as exc:  # noqa: BLE001
				last_error = f"{url}: {exc}"

		if last_error:
			raise RuntimeError(last_error)
		return None


class DashboardApp:
	"""Render the live telemetry dashboard using Rich components."""

	def __init__(
		self,
		console: Console,
		client: TelemetryClient,
		refresh_interval: float = 2.0,
		show_system: bool = True,
	) -> None:
		self.console = console
		self.client = client
		self.refresh_interval = refresh_interval
		self.show_system = show_system
		self.state = DashboardState()

	def run(self) -> None:
		"""Begin the dashboard loop until interrupted."""

		with Live(
			self._render(sys_metrics=self._system_metrics()),
			refresh_per_second=4,
			screen=True,
			console=self.console,
		) as live:
			while True:
				try:
					snapshot = self.client.fetch_snapshot()
					if snapshot:
						self.state.update(snapshot)
					else:
						self.state.note_error("Telemetry unavailable")
				except Exception as exc:  # noqa: BLE001
					self.state.note_error(str(exc))

				sys_metrics = self._system_metrics()
				live.update(self._render(sys_metrics))
				time.sleep(self.refresh_interval)

	# ------------------------------------------------------------------
	# Rendering helpers
	# ------------------------------------------------------------------
	def _render(self, sys_metrics: Optional[Dict[str, Any]]) -> Layout:
		layout = Layout()
		layout.split_column(
			Layout(name="header", size=5),
			Layout(name="body", ratio=1),
			Layout(name="footer", size=3),
		)
		layout["body"].split_row(
			Layout(name="left", ratio=2),
			Layout(name="right", ratio=3),
		)
		layout["left"].split_column(
			Layout(name="usage", size=9),
			Layout(name="providers", ratio=2),
			Layout(name="history", size=7),
		)
		layout["right"].split_column(
			Layout(name="tasks", ratio=2),
			Layout(name="events", ratio=1),
			Layout(name="system", size=7),
		)

		layout["header"].update(self._render_header())
		layout["usage"].update(self._render_usage_summary())
		layout["providers"].update(self._render_providers())
		layout["history"].update(self._render_history())
		layout["tasks"].update(self._render_tasks())
		layout["events"].update(self._render_events())
		layout["system"].update(self._render_system(sys_metrics))
		layout["footer"].update(self._render_footer())
		return layout

	def _render_header(self) -> Panel:
		snapshot = self.state.snapshot
		if not snapshot:
			return Panel("Awaiting first snapshot...", style="yellow")

		uptime = format_duration(snapshot.get("uptime_seconds", 0))
		phase = snapshot.get("phase", "UNKNOWN")
		detail = snapshot.get("phase_detail", "")
		runtime_mode = snapshot.get("runtime_mode", "legacy")
		total_calls = snapshot.get("total_calls", 0)
		total_failures = snapshot.get("total_failures", 0)

		header = Table.grid(expand=True)
		header.add_column(justify="left")
		header.add_column(justify="center")
		header.add_column(justify="right")
		header.add_row(
			f"[bold]Phase:[/] {phase} {detail}",
			f"[bold]Runtime:[/] {runtime_mode}",
			f"[bold]Uptime:[/] {uptime}",
		)
		header.add_row(
			f"[green]Calls[/]: {total_calls}",
			f"[red]Failures[/]: {total_failures}",
			f"[bold]Last call:[/] {snapshot.get('last_call_at', '—')}",
		)
		return Panel(header, title="Sophia Telemetry", border_style="cyan")

	def _render_providers(self) -> Panel:
		table = Table(title="Providers", box=box.SIMPLE_HEAVY, expand=True)
		table.add_column("Name", justify="left", style="bold")
		table.add_column("Mode", justify="center")
		table.add_column("Calls", justify="right")
		table.add_column("Prompt", justify="right")
		table.add_column("Completion", justify="right")
		table.add_column("Cost $", justify="right")

		snapshot = self.state.snapshot or {}
		providers: Iterable[Dict[str, Any]] = snapshot.get("provider_stats", [])
		for provider in providers:
			table.add_row(
				provider.get("name", "n/a"),
				provider.get("mode", "?"),
				f"{provider.get('calls', 0):,}",
				format_tokens(provider.get("prompt_tokens", 0)),
				format_tokens(provider.get("completion_tokens", 0)),
				f"{provider.get('cost_usd', 0.0):.4f}",
			)

		if not providers:
			table.add_row("–", "–", "0", "0", "0", "0.0000")

		summary = Table.grid(expand=True)
		summary.add_column(justify="left")
		summary.add_column(justify="right")
		summary.add_row("Online tokens", format_tokens(snapshot.get("online_tokens", 0)))
		summary.add_row("Offline tokens", format_tokens(snapshot.get("offline_tokens", 0)))
		summary.add_row("Hybrid tokens", format_tokens(snapshot.get("hybrid_tokens", 0)))

		inner = Group(
			Align.center(table),
			Panel(summary, border_style="dim", box=box.SQUARE, title="Token Split"),
		)
		return Panel(inner, border_style="green")

	def _render_usage_summary(self) -> Panel:
		if not self.state.snapshot or not self.state.usage:
			return Panel("Waiting for telemetry...", border_style="yellow", title="Usage Overview")

		usage = self.state.usage
		snapshot = self.state.snapshot
		table = Table.grid(expand=True)
		table.add_column()
		table.add_column(justify="right")
		table.add_row("Total tokens", format_tokens(usage.total_tokens))
		table.add_row("Prompt tokens", format_tokens(usage.prompt_tokens))
		table.add_row("Completion tokens", format_tokens(usage.completion_tokens))
		table.add_row("Total cost", f"${usage.cost_usd:.4f}")

		phase = snapshot.get("phase", "UNKNOWN")
		runtime = snapshot.get("runtime_mode", "legacy")
		total_calls = snapshot.get("total_calls", 0)
		total_failures = snapshot.get("total_failures", 0)
		last_call = snapshot.get("last_call_at") or "—"
		tips = Text(
			"\n".join(
				[
					f"Phase: {phase} · Runtime: {runtime}",
					f"LLM calls: {total_calls:,} · Failures: {total_failures:,}",
					f"Last call at {last_call if last_call else '—'}",
					"If usage spikes unexpectedly, pause the queue or switch to offline providers to stay on budget.",
				]
			),
			style="white",
		)

		body = Group(table, Align.left(tips))
		return Panel(body, title="Usage Overview", border_style="cyan")

	def _render_history(self) -> Panel:
		if not self.state.tokens_history:
			return Panel("History pending...", border_style="yellow")

		tokens = self.state.tokens_history[-1]
		prev_tokens = self.state.tokens_history[-2] if len(self.state.tokens_history) > 1 else tokens
		delta_tokens = tokens - prev_tokens

		cost = self.state.cost_history[-1]
		prev_cost = self.state.cost_history[-2] if len(self.state.cost_history) > 1 else cost
		delta_cost = cost - prev_cost

		uptime = self.state.snapshot.get("uptime_seconds", 0) if self.state.snapshot else 0
		projected = project_monthly_spend(cost, uptime)

		grid = Table.grid(expand=True)
		grid.add_column()
		grid.add_column(justify="right")
		grid.add_row("Total tokens", format_tokens(tokens))
		grid.add_row("Δ tokens", format_tokens(delta_tokens))
		grid.add_row("Total cost", f"${cost:.4f}")
		grid.add_row("Δ cost", f"${delta_cost:.4f}")
		grid.add_row("Projected 30d", f"${projected:.2f}")
		grid.add_row("Budget goal", "$10.00")

		style = "red" if projected > 10 else "green"
		return Panel(grid, title="Budget", border_style=style)

	def _render_tasks(self) -> Panel:
		snapshot = self.state.snapshot or {}
		tasks = snapshot.get("tasks", [])
		table = Table(title="Task Queue", box=box.MINIMAL_DOUBLE_HEAD, expand=True)
		table.add_column("ID", justify="right")
		table.add_column("Name")
		table.add_column("Status", justify="center")
		table.add_column("Updated", justify="right")
		for task in tasks[:8]:
			status = task.get("status", "?")
			color = {
				"pending": "yellow",
				"running": "cyan",
				"completed": "green",
				"failed": "red",
				"cancelled": "magenta",
			}.get(status, "white")
			table.add_row(
				str(task.get("task_id", "?")),
				task.get("name", "task"),
				f"[{color}]{status}[/{color}]",
				task.get("updated_at", "–"),
			)
		if not tasks:
			table.add_row("–", "No tasks", "–", "–")
		return Panel(table, border_style="blue")

	def _render_events(self) -> Panel:
		snapshot = self.state.snapshot or {}
		events = snapshot.get("recent_events", [])
		table = Table(title="Recent Events", box=box.SIMPLE, expand=True)
		table.add_column("Time")
		table.add_column("Source")
		table.add_column("Message")
		for event in events[-10:]:
			level = event.get("level", "info")
			color = {"info": "white", "warning": "yellow", "error": "red"}.get(level, "white")
			table.add_row(
				event.get("timestamp", "–"),
				event.get("source", "kernel"),
				f"[{color}]{event.get('message', '')}[/{color}]",
			)
		if not events:
			table.add_row("–", "–", "No events yet")
		return Panel(table, border_style="magenta")

	def _render_system(self, metrics: Optional[Dict[str, Any]]) -> Panel:
		if not self.show_system or not metrics:
			return Panel("System metrics disabled", border_style="dim")

		table = Table.grid(expand=True)
		table.add_row(f"CPU: {metrics['cpu']}%", f"RAM: {metrics['ram']}%")
		table.add_row(
			f"Disk: {metrics['disk']}%",
			f"Net ↑ {metrics['net_sent']} MB / ↓ {metrics['net_recv']} MB",
		)
		return Panel(table, title="Host", border_style="cyan")

	def _render_footer(self) -> Panel:
		status = Text()
		if self.state.error_message:
			status.append(f"⚠️  {self.state.error_message}", style="yellow")
		elif self.state.snapshot:
			status.append("Connected", style="green")
		else:
			status.append("Connecting...", style="yellow")

		info = Text()
		info.append(" Ctrl+C to exit • ")
		info.append(f"Refresh {self.refresh_interval:.1f}s • ")
		info.append(f"Endpoint {self.client.base_url}")

		grid = Table.grid(expand=True)
		grid.add_column(ratio=1)
		grid.add_column(ratio=2)
		grid.add_row(status, info)
		return Panel(grid, border_style="white")

	# ------------------------------------------------------------------
	# Utilities
	# ------------------------------------------------------------------
	def _system_metrics(self) -> Optional[Dict[str, Any]]:
		if not self.show_system or psutil is None:
			return None

		try:
			return {
				"cpu": psutil.cpu_percent(interval=None),
				"ram": psutil.virtual_memory().percent,
				"disk": psutil.disk_usage("/").percent,
				"net_sent": psutil.net_io_counters().bytes_sent // 1024 // 1024,
				"net_recv": psutil.net_io_counters().bytes_recv // 1024 // 1024,
			}
		except Exception:  # noqa: BLE001
			return None


def parse_args() -> argparse.Namespace:
	"""Parse CLI arguments for the dashboard."""

	parser = argparse.ArgumentParser(description="Sophia Telemetry Dashboard")
	parser.add_argument(
		"--server",
		default=DEFAULT_SERVER,
		help="Base URL of the Sophia Web UI server (default: %(default)s)",
	)
	parser.add_argument(
		"--refresh",
		type=float,
		default=2.0,
		help="Refresh interval in seconds",
	)
	parser.add_argument(
		"--no-system",
		action="store_true",
		help="Disable host system metrics panel",
	)
	parser.add_argument(
		"--timeout",
		type=float,
		default=2.0,
		help="HTTP timeout for telemetry requests",
	)
	return parser.parse_args()


def main() -> None:
	"""Entrypoint for invoking the CLI programmatically."""

	args = parse_args()
	console = Console()
	client = TelemetryClient(args.server, timeout=max(0.2, args.timeout))
	app = DashboardApp(
		console=console,
		client=client,
		refresh_interval=max(0.5, args.refresh),
		show_system=not args.no_system,
	)
	try:
		app.run()
	except KeyboardInterrupt:  # pragma: no cover - interactive
		console.print("\n[red]Dashboard stopped by user.[/red]")


if __name__ == "__main__":
	sys.exit(main())
