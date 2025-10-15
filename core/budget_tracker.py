"""
Budget Tracker - sledování spotřeby tokenů a času.

Prevence vyčerpání rozpočtu během mise:
- Tracking tokenů per step
- Tracking času per step
- Varování při 80% threshold
- Validace před započetím kroku
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import time


@dataclass
class BudgetWarning:
    """Varování o stavu rozpočtu."""
    
    level: str  # "info", "warning", "critical"
    message: str
    tokens_remaining: int
    time_remaining: float


class BudgetTracker:
    """
    Sleduje spotřebu tokenů a času a varuje před vyčerpáním.
    
    FEATURES:
    - Token tracking per step
    - Time tracking per step
    - Warning at 80% threshold
    - Critical alert at 95% threshold
    - Budget validation before step execution
    """
    
    def __init__(
        self,
        max_tokens: int = 100000,
        max_time_seconds: int = 3600,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95
    ):
        """
        Inicializuje BudgetTracker.
        
        Args:
            max_tokens: Maximum tokenů pro misi
            max_time_seconds: Maximum času (sekundy)
            warning_threshold: Threshold pro varování (0.0 - 1.0)
            critical_threshold: Threshold pro kritické varování (0.0 - 1.0)
        """
        self.max_tokens = max_tokens
        self.max_time_seconds = max_time_seconds
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
        self.tokens_used = 0
        self.time_elapsed = 0.0
        self.step_costs: Dict[int, Dict[str, Any]] = {}
        self.start_time = time.time()
        self.warnings_issued: list[BudgetWarning] = []
    
    def record_step_cost(
        self,
        step_id: int,
        tokens: int,
        seconds: float,
        step_description: str = ""
    ) -> None:
        """
        Zaznamená náklady kroku.
        
        Args:
            step_id: ID kroku
            tokens: Počet tokenů spotřebovaných
            seconds: Počet sekund strávených
            step_description: Popis kroku (volitelné)
        """
        self.tokens_used += tokens
        self.time_elapsed += seconds
        
        self.step_costs[step_id] = {
            "tokens": tokens,
            "seconds": seconds,
            "description": step_description,
            "timestamp": time.time()
        }
    
    def check_budget(self, estimated_tokens: int = 0) -> Dict[str, Any]:
        """
        Zkontroluje, zda je dostatek rozpočtu.
        
        Args:
            estimated_tokens: Odhadované tokeny pro následující krok
        
        Returns:
            {
                "can_proceed": bool,
                "warning": Optional[BudgetWarning],
                "tokens_remaining": int,
                "time_remaining": float,
                "tokens_used_percent": float,
                "time_used_percent": float
            }
        """
        tokens_remaining = self.max_tokens - self.tokens_used
        current_time_elapsed = time.time() - self.start_time
        time_remaining = self.max_time_seconds - current_time_elapsed
        
        tokens_used_percent = self.tokens_used / self.max_tokens
        time_used_percent = current_time_elapsed / self.max_time_seconds
        
        # Určíme, zda můžeme pokračovat
        can_proceed = (
            tokens_remaining >= estimated_tokens and
            time_remaining > 60  # Aspoň 1 minuta
        )
        
        # Generuj varování
        warning = self._generate_warning(
            tokens_remaining,
            time_remaining,
            estimated_tokens,
            tokens_used_percent,
            time_used_percent
        )
        
        if warning:
            self.warnings_issued.append(warning)
        
        return {
            "can_proceed": can_proceed,
            "warning": warning,
            "tokens_remaining": tokens_remaining,
            "time_remaining": time_remaining,
            "tokens_used_percent": tokens_used_percent,
            "time_used_percent": time_used_percent
        }
    
    def _generate_warning(
        self,
        tokens_remaining: int,
        time_remaining: float,
        estimated_tokens: int,
        tokens_used_percent: float,
        time_used_percent: float
    ) -> Optional[BudgetWarning]:
        """Generuje varování podle stavu rozpočtu."""
        
        # CRITICAL: Nedostatek pro estimated tokens (má prioritu)
        if tokens_remaining < estimated_tokens:
            return BudgetWarning(
                level="critical",
                message=f"❌ NEDOSTATEK TOKENŮ: Potřeba {estimated_tokens}, zbývá {tokens_remaining}",
                tokens_remaining=tokens_remaining,
                time_remaining=time_remaining
            )
        
        # CRITICAL: Překročen critical threshold
        if tokens_used_percent >= self.critical_threshold:
            return BudgetWarning(
                level="critical",
                message=f"🚨 KRITICKY NÍZKÝ ROZPOČET TOKENŮ: {tokens_remaining}/{self.max_tokens} zbývá",
                tokens_remaining=tokens_remaining,
                time_remaining=time_remaining
            )
        
        if time_used_percent >= self.critical_threshold:
            return BudgetWarning(
                level="critical",
                message=f"🚨 KRITICKY MÁLO ČASU: {time_remaining:.0f}s zbývá",
                tokens_remaining=tokens_remaining,
                time_remaining=time_remaining
            )
        
        # WARNING: Překročen warning threshold
        if tokens_used_percent >= self.warning_threshold:
            return BudgetWarning(
                level="warning",
                message=f"⚠️  NÍZKÝ ROZPOČET TOKENŮ: {tokens_remaining}/{self.max_tokens} zbývá ({tokens_used_percent*100:.1f}% spotřebováno)",
                tokens_remaining=tokens_remaining,
                time_remaining=time_remaining
            )
        
        if time_used_percent >= self.warning_threshold:
            return BudgetWarning(
                level="warning",
                message=f"⚠️  MÁLO ČASU: {time_remaining:.0f}s zbývá ({time_used_percent*100:.1f}% spotřebováno)",
                tokens_remaining=tokens_remaining,
                time_remaining=time_remaining
            )
        
        # Žádné varování
        return None
    
    def get_summary(self) -> str:
        """
        Vrátí přehled spotřeby.
        
        Returns:
            Formátovaný string se souhrnem
        """
        current_time_elapsed = time.time() - self.start_time
        
        tokens_percent = (self.tokens_used / self.max_tokens) * 100
        time_percent = (current_time_elapsed / self.max_time_seconds) * 100
        
        return (
            f"📊 BUDGET SUMMARY:\n"
            f"  Tokeny: {self.tokens_used}/{self.max_tokens} ({tokens_percent:.1f}%)\n"
            f"  Čas: {current_time_elapsed:.0f}s/{self.max_time_seconds}s ({time_percent:.1f}%)\n"
            f"  Kroky: {len(self.step_costs)} dokončeno\n"
            f"  Varování: {len(self.warnings_issued)}"
        )
    
    def get_detailed_summary(self) -> Dict[str, Any]:
        """
        Vrátí detailní souhrn jako dictionary.
        
        Returns:
            Dictionary se všemi metriky
        """
        current_time_elapsed = time.time() - self.start_time
        
        return {
            "tokens": {
                "used": self.tokens_used,
                "max": self.max_tokens,
                "remaining": self.max_tokens - self.tokens_used,
                "percent": (self.tokens_used / self.max_tokens) * 100
            },
            "time": {
                "elapsed": current_time_elapsed,
                "max": self.max_time_seconds,
                "remaining": self.max_time_seconds - current_time_elapsed,
                "percent": (current_time_elapsed / self.max_time_seconds) * 100
            },
            "steps": {
                "count": len(self.step_costs),
                "costs": self.step_costs
            },
            "warnings": {
                "count": len(self.warnings_issued),
                "list": [
                    {
                        "level": w.level,
                        "message": w.message,
                        "tokens_remaining": w.tokens_remaining,
                        "time_remaining": w.time_remaining
                    }
                    for w in self.warnings_issued
                ]
            }
        }
    
    def get_step_cost(self, step_id: int) -> Optional[Dict[str, Any]]:
        """Vrátí náklady konkrétního kroku."""
        return self.step_costs.get(step_id)
    
    def get_average_step_cost(self) -> Dict[str, float]:
        """
        Vrátí průměrné náklady na krok.
        
        Returns:
            {"tokens": float, "seconds": float}
        """
        if not self.step_costs:
            return {"tokens": 0.0, "seconds": 0.0}
        
        total_tokens = sum(cost["tokens"] for cost in self.step_costs.values())
        total_seconds = sum(cost["seconds"] for cost in self.step_costs.values())
        count = len(self.step_costs)
        
        return {
            "tokens": total_tokens / count,
            "seconds": total_seconds / count
        }
    
    def estimate_remaining_steps(self) -> int:
        """
        Odhadne kolik kroků ještě můžeme zvládnout.
        
        Returns:
            Odhadovaný počet zbývajících kroků
        """
        avg = self.get_average_step_cost()
        
        if avg["tokens"] == 0:
            return 999  # Ještě jsme nic nespotřebovali
        
        tokens_remaining = self.max_tokens - self.tokens_used
        current_time_elapsed = time.time() - self.start_time
        time_remaining = self.max_time_seconds - current_time_elapsed
        
        steps_by_tokens = int(tokens_remaining / avg["tokens"])
        steps_by_time = int(time_remaining / avg["seconds"]) if avg["seconds"] > 0 else 999
        
        return min(steps_by_tokens, steps_by_time)
    
    def reset(self) -> None:
        """Resetuje všechny countery (pro novou misi)."""
        self.tokens_used = 0
        self.time_elapsed = 0.0
        self.step_costs.clear()
        self.warnings_issued.clear()
        self.start_time = time.time()
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serializuje stav do dictionary.
        
        Returns:
            Dictionary pro JSON serialization
        """
        current_time_elapsed = time.time() - self.start_time
        
        return {
            "max_tokens": self.max_tokens,
            "max_time_seconds": self.max_time_seconds,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "tokens_used": self.tokens_used,
            "time_elapsed": current_time_elapsed,
            "step_costs": self.step_costs,
            "warnings_count": len(self.warnings_issued)
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'BudgetTracker':
        """
        Deserializuje z dictionary.
        
        Args:
            data: Dictionary s uloženým stavem
        
        Returns:
            Nová instance BudgetTracker
        """
        tracker = cls(
            max_tokens=data["max_tokens"],
            max_time_seconds=data["max_time_seconds"],
            warning_threshold=data.get("warning_threshold", 0.8),
            critical_threshold=data.get("critical_threshold", 0.95)
        )
        
        tracker.tokens_used = data["tokens_used"]
        tracker.time_elapsed = data.get("time_elapsed", 0.0)
        tracker.step_costs = data.get("step_costs", {})
        
        # Adjust start_time based on elapsed
        tracker.start_time = time.time() - tracker.time_elapsed
        
        return tracker
