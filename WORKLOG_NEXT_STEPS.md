Recent session summary & next steps

This file records the concise next steps following the recent session where local-only operation, planner/evaluator hardening, dashboard scaffold and guardian were implemented.

Summary of immediate next steps (high priority):

- Confirm background `.venv` pip install completed (langfuse, httpx). Monitor logs and the background pip process; restart guardian/supervisor if needed.
- Verify `tool_langfuse` no longer raises ModuleNotFoundError and allow `plugins/tool_langfuse.py` to initialize when present.
- Add `/api/benchmarks` endpoint and persistent storage (ModelManager extension) to expose benchmark history to the dashboard.
- Enhance dashboard UI to show current queue, active task, last plan steps, latest LLM responses, and benchmark history.
- Implement a minimal `plugins/tool_model_manager.py` to list local models, schedule benchmarks, and trigger model downloads.
- Expand integration tests: add bench-history endpoint tests and a test verifying planner JSON extraction across common edge cases (multiple JSON blocks, code fences).

Lower priority / future:

- Implement sandboxed self-tuning pipeline (cognitive_self_tuning & cognitive_reflection) to auto-suggest prompt changes and evaluate them via `tool_model_evaluator`.
- Add CI tests to validate offline-mode (SOPHIA_FORCE_LOCAL_ONLY=true) and guardian/supervisor restart behavior.
- Polish WebUI with controls (pause/resume, allow_cloud toggle) and authentication if exposed externally.

Notes:
- I attempted to update `WORKLOG.md` but the file is large and context-matching failed; creating this shorter companion file preserves the recent summary and action items.
- If you want the longer WORKLOG.md updated instead, I can patch it directly (I'll read the tail and append with an apply_patch edit). Prefer append vs in-place edits to avoid merge conflicts.

Status: ready to continue. If you confirm, I will:
1) check the background pip install status, 2) restart guardian/supervisor if needed, 3) add `/api/benchmarks` and a small ModelManager DB table, and 4) implement dashboard enhancements in the next commit.
