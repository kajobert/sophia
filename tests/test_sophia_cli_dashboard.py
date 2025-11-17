"""Tests for the terminal telemetry dashboard helpers."""

from __future__ import annotations

from typing import List

from sophia_cli_dashboard import (
    HISTORY_LIMIT,
    DashboardState,
    UsageSummary,
    format_duration,
    format_tokens,
    project_monthly_spend,
)


def test_format_duration_represents_hours_minutes_seconds() -> None:
    assert format_duration(3660) == "1h 1m"
    assert format_duration(120) == "2m 0s"
    assert format_duration(45) == "45s"


def test_format_tokens_adds_thousands_separator() -> None:
    assert format_tokens(123456) == "123,456"
    assert format_tokens(0) == "0"


def test_project_monthly_spend_handles_zero_and_positive_uptime() -> None:
    assert project_monthly_spend(5.0, 0) == 5.0
    projected = project_monthly_spend(2.0, 3600)
    assert projected == 2.0 * 24 * 30


def test_dashboard_state_update_tracks_history_and_clears_error() -> None:
    state = DashboardState()
    state.error_message = "previous error"
    snapshot = {
        "total_tokens_prompt": 1000,
        "total_tokens_completion": 500,
        "total_cost_usd": 1.25,
    }
    state.update(snapshot)

    assert state.snapshot == snapshot
    assert list(state.tokens_history)[-1] == 1500
    assert list(state.cost_history)[-1] == 1.25
    assert state.usage is not None
    assert state.usage.total_tokens == 1500
    assert state.usage.cost_usd == 1.25
    assert state.error_message is None


def test_dashboard_state_fallback_fields_and_history_limit() -> None:
    state = DashboardState()
    for idx in range(HISTORY_LIMIT + 5):
        snapshot = {"online_tokens": idx, "cost_usd": idx / 10}
        state.update(snapshot)

    tokens: List[float] = list(state.tokens_history)
    costs: List[float] = list(state.cost_history)

    assert len(tokens) == HISTORY_LIMIT
    assert len(costs) == HISTORY_LIMIT
    assert tokens[-1] == HISTORY_LIMIT + 4
    assert costs[-1] == (HISTORY_LIMIT + 4) / 10


def test_dashboard_state_note_error_sets_message() -> None:
    state = DashboardState()
    state.note_error("network issue")
    assert state.error_message == "network issue"


def test_usage_summary_handles_multiple_sources() -> None:
    snapshot = {
        "total_tokens_prompt": 600,
        "total_tokens_completion": 400,
        "total_cost_usd": 3.5,
        "online_tokens": 700,
        "offline_tokens": 200,
        "hybrid_tokens": 100,
    }
    summary = UsageSummary.from_snapshot(snapshot)
    assert summary.prompt_tokens == 600
    assert summary.completion_tokens == 400
    assert summary.total_tokens == 700 + 200 + 100  # mode total wins
    assert summary.cost_usd == 3.5


def test_usage_summary_falls_back_to_prompt_plus_completion() -> None:
    snapshot = {
        "prompt_tokens": 250,
        "completion_tokens": 125,
        "total_cost": 0.75,
    }
    summary = UsageSummary.from_snapshot(snapshot)
    assert summary.total_tokens == 375
    assert summary.cost_usd == 0.75
