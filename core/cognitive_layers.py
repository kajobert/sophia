from typing import Dict, Any, Optional
import marko
import os
import logging

from core.memory_systems import ShortTermMemory, LongTermMemory
from core.context import SharedContext

logger = logging.getLogger(__name__)


class ReptilianBrain:
    """Instinct layer: quick filtering, safety checks, basic structuring.

    For MVP this class reads `docs/DNA.md` (if present) and applies a tiny
    rule set. Heavy logic is intentionally omitted and left as stubs.
    """

    def __init__(self, dna_path: str = "docs/DNA.md"):
        self.dna_path = dna_path
        self.rules = self._load_dna()

    def _load_dna(self) -> Dict[str, Any]:
        if not os.path.exists(self.dna_path):
            logger.info("DNA.md not found, using default empty rules")
            return {}
        try:
            with open(self.dna_path, "r", encoding="utf-8") as f:
                md = f.read()
            # Use marko to parse markdown into an AST; for MVP we'll simply keep text
            ast = marko.Markdown().convert(md)
            return {"raw": md, "html": ast}
        except Exception as e:
            logger.exception("Failed to load DNA.md: %s", e)
            return {}

    def process_input(self, context: SharedContext) -> SharedContext:
        # Basic safety check (stub): reject empty prompts
        prompt = (context.original_prompt or "").strip()
        if not prompt:
            context.feedback = "Rejected: empty prompt"
            context.payload["reptilian"] = {"accepted": False}
            return context

        # Example of structuring: minimal classification by length
        classification = "short" if len(prompt) < 200 else "long"
        context.payload.setdefault("preprocessed", {})["classification"] = (
            classification
        )
        context.payload["reptilian"] = {
            "accepted": True,
            "classification": classification,
        }
        return context


class MammalianBrain:
    """Subconscious layer: enriches input with long-term memory/context."""

    def __init__(self, long_term_memory: Optional[LongTermMemory] = None):
        self.ltm = long_term_memory or LongTermMemory()

    def process_input(self, context: SharedContext) -> SharedContext:
        # Use the prompt to search long-term memory for context
        prompt = context.original_prompt or ""
        results = self.ltm.search(prompt, top_k=3)
        context.payload.setdefault("mammalian", {})["ltm_matches"] = results
        return context


class Neocortex:
    """Top-level layer: strategy and planning. Minimal wrapper that stores state
    in ShortTermMemory and can call a planner (injected) when needed.
    """

    def __init__(
        self, short_term_memory: Optional[ShortTermMemory] = None, planner=None
    ):
        self.stm = short_term_memory or ShortTermMemory()
        self.planner = planner

    def process_input(self, context: SharedContext) -> SharedContext:
        # Save current incoming context to short-term memory
        self.stm.set(
            context.session_id,
            {"original_prompt": context.original_prompt, "payload": context.payload},
        )

        # If a planner is provided, request a plan
        if self.planner:
            try:
                plan_context = self.planner.run_task(context)
                context.payload["plan"] = plan_context.payload.get("plan")
            except Exception as e:
                logger.exception("Planner failed inside Neocortex: %s", e)
                context.feedback = f"Planner error: {e}"
        else:
            context.payload.setdefault("plan", [])

        # store plan in STM
        self.stm.update(context.session_id, {"plan": context.payload.get("plan")})
        return context
