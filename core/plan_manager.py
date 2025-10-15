"""
Plan Manager - Proaktivní plánování mise.

Tento modul transformuje reaktivní loop na proaktivní exekuci plánu.
Vytváří strukturovaný plán pomocí LLM, sleduje závislosti a pokrok.

ARCHITEKTURA:
- PlanStep: Atomický krok s ID, popisem, závislostmi, statusem
- PlanManager: Vytváření plánu přes LLM, tracking pokroku, dependency resolution

KLÍČOVÉ VLASTNOSTI:
- Závislosti mezi kroky (step 3 nemůže začít před dokončením step 1, 2)
- Progress tracking (kolik % dokončeno)
- Token estimation (kolik tokenů pravděpodobně spotřebuje každý krok)
- Serializace/deserializace pro persistence

POUŽITÍ:
    pm = PlanManager(llm_manager, project_root=".")
    
    # Vytvoř plán
    plan = await pm.create_plan("Refactoruj orchestrator.py")
    
    # Iteruj kroky
    while not pm.is_plan_complete():
        step = pm.get_next_step()  # Respektuje závislosti
        if step:
            pm.mark_step_in_progress(step.id)
            # ... proveď krok ...
            pm.mark_step_completed(step.id, result, tokens_used)

THREAD SAFETY: Není thread-safe!
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from core.rich_printer import RichPrinter
import json
import re


@dataclass
class PlanStep:
    """
    Reprezentuje jeden atomický krok v plánu.
    
    Attributes:
        id: Unikátní ID kroku (1-indexed)
        description: Lidsky čitelný popis co má být uděláno
        status: Aktuální stav ("pending", "in_progress", "completed", "failed", "skipped")
        dependencies: List ID kroků, které musí být dokončeny před tímto krokem
        estimated_tokens: Odhad tokenů pro tento krok (0 = neznámé)
        actual_tokens: Skutečně spotřebované tokeny (0 = ještě neproběhlo)
        result: Výsledek provedení (None pokud ještě neproběhlo)
        error: Chybová hláška (None pokud úspěch nebo ještě neproběhlo)
    """
    id: int
    description: str
    status: str = "pending"
    dependencies: List[int] = field(default_factory=list)
    estimated_tokens: int = 0
    actual_tokens: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konverze na dictionary pro serializaci."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlanStep':
        """Vytvoří PlanStep z dictionary."""
        return cls(**data)


class PlanManager:
    """
    Spravuje plán mise - vytváření, sledování, aktualizace.
    
    ARCHITEKTONICKÉ ROZHODNUTÍ:
    - Plán je vytvořen JEDNOU na začátku mise (může být replanován při selhání)
    - Kroky jsou prováděny v pořadí respektujícím závislosti
    - Progress je sledován v reálném čase
    """
    
    def __init__(self, llm_manager, project_root: str = "."):
        """
        Inicializace PlanManager.
        
        Args:
            llm_manager: Instance LLMManager pro komunikaci s LLM
            project_root: Kořenový adresář projektu
        """
        self.llm_manager = llm_manager
        self.project_root = project_root
        self.steps: List[PlanStep] = []
        self.current_step_index = 0
        self.plan_created_at: Optional[str] = None
    
    async def create_plan(
        self, 
        mission_goal: str, 
        context: str = "",
        max_steps: int = 10
    ) -> List[PlanStep]:
        """
        Vytvoří plán pro daný cíl mise pomocí LLM.
        
        Args:
            mission_goal: Cíl mise (např. "Refactoruj orchestrator.py")
            context: Dodatečný kontext (volitelný)
            max_steps: Maximální počet kroků v plánu
        
        Returns:
            Seznam PlanStep objektů
        
        Raises:
            ValueError: Pokud LLM nevygeneruje validní plán
        """
        RichPrinter.info("📋 Vytvářím plán mise...")
        
        # Prompt pro LLM
        planning_prompt = self._build_planning_prompt(
            mission_goal, context, max_steps
        )
        
        # Zavolej LLM (použij "powerful" model pro strategické myšlení)
        try:
            model = self.llm_manager.get_llm("powerful")
        except (ValueError, FileNotFoundError):
            # Fallback na default model pokud "powerful" není k dispozici
            RichPrinter.warning("⚠️  'powerful' model nedostupný, používám default")
            model = self.llm_manager.get_llm(self.llm_manager.default_llm_name)
        
        response, usage = await model.generate_content_async(planning_prompt)
        
        # Parse JSON z odpovědi
        plan_data = self._parse_plan_from_response(response)
        
        if not plan_data or "steps" not in plan_data:
            raise ValueError("LLM nevygeneroval validní plán")
        
        # Konverze na PlanStep objekty
        self.steps = [
            PlanStep(
                id=step["id"],
                description=step["description"],
                dependencies=step.get("dependencies", []),
                estimated_tokens=step.get("estimated_tokens", 500)
            )
            for step in plan_data["steps"][:max_steps]  # Limit kroků
        ]
        
        self.plan_created_at = datetime.now().isoformat()
        
        # Validace plánu
        self._validate_plan()
        
        # Zobraz plán
        self._display_plan()
        
        return self.steps
    
    def _build_planning_prompt(
        self, 
        mission_goal: str, 
        context: str,
        max_steps: int
    ) -> str:
        """Sestaví prompt pro LLM."""
        return f"""Jsi strategický plánovač pro AI agenta. Rozlož následující úkol na konkrétní, proveditelné kroky.

ÚKOL:
{mission_goal}

KONTEXT:
{context if context else "Žádný dodatečný kontext."}

POŽADAVKY NA PLÁN:
1. Každý krok musí být ATOMICKÝ (jedna jasná akce)
2. Každý krok musí být TESTOVATELNÝ (lze ověřit úspěch/selhání)
3. Kroky musí být seřazeny LOGICKY (respektuj závislosti)
4. Odhadni SLOŽITOST každého kroku (tokens: 100-2000)
5. Maximálně {max_steps} kroků
6. Pokud krok závisí na jiném kroku, uveď to v dependencies

PŘÍKLAD DOBRÉHO PLÁNU:
{{
  "steps": [
    {{
      "id": 1,
      "description": "Přečti soubor orchestrator.py a analyzuj jeho strukturu",
      "dependencies": [],
      "estimated_tokens": 300
    }},
    {{
      "id": 2,
      "description": "Identifikuj duplicitní kód a navrhni refaktoring",
      "dependencies": [1],
      "estimated_tokens": 800
    }},
    {{
      "id": 3,
      "description": "Implementuj refactored_orchestrator.py s čistším kódem",
      "dependencies": [2],
      "estimated_tokens": 1200
    }},
    {{
      "id": 4,
      "description": "Spusť testy a ověř že refaktoring nic nerozbil",
      "dependencies": [3],
      "estimated_tokens": 400
    }}
  ]
}}

FORMÁT ODPOVĚDI (POUZE JSON, žádný markdown):
{{
  "steps": [
    {{
      "id": 1,
      "description": "...",
      "dependencies": [],
      "estimated_tokens": 500
    }},
    ...
  ]
}}
"""
    
    def _parse_plan_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON plánu z LLM odpovědi.
        
        Umí zpracovat:
        - Čistý JSON
        - JSON v markdown code blocku
        - JSON s extra textem před/po
        """
        # Pokus 1: Najdi JSON v markdown code blocku
        json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                RichPrinter.warning(f"⚠️  JSON v code blocku není validní: {e}")
        
        # Pokus 2: Najdi první validní JSON objekt
        brace_start = response.find('{')
        if brace_start != -1:
            # Najdi matching uzavírací závorku
            brace_count = 0
            for i in range(brace_start, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = response[brace_start:i+1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            RichPrinter.warning(f"⚠️  Extrahovaný JSON není validní: {e}")
                        break
        
        # Pokus 3: Zkus parsovat celou odpověď jako JSON
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            RichPrinter.error("❌ Nepodařilo se zparsovat plán z LLM odpovědi")
            RichPrinter.error(f"Odpověď LLM:\n{response[:500]}...")
            return None
    
    def _validate_plan(self):
        """
        Validuje plán na konzistenci.
        
        Raises:
            ValueError: Pokud plán není validní
        """
        if not self.steps:
            raise ValueError("Plán je prázdný")
        
        # Kontrola unikátních ID
        step_ids = [s.id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Plán obsahuje duplicitní ID kroků")
        
        # Kontrola závislostí (závislosti musí být na existující kroky)
        for step in self.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ValueError(
                        f"Krok {step.id} má závislost na neexistujícím kroku {dep_id}"
                    )
                # Závislost nesmí být na sebe sama
                if dep_id == step.id:
                    raise ValueError(f"Krok {step.id} nemůže záviset sám na sobě")
        
        # Kontrola cyklických závislostí
        self._check_for_cycles()
    
    def _check_for_cycles(self):
        """
        Kontrola cyklických závislostí pomocí DFS.
        
        Raises:
            ValueError: Pokud existuje cyklus
        """
        def has_cycle(step_id: int, visited: set, rec_stack: set) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next((s for s in self.steps if s.id == step_id), None)
            if step:
                for dep_id in step.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id, visited, rec_stack):
                            return True
                    elif dep_id in rec_stack:
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        visited = set()
        for step in self.steps:
            if step.id not in visited:
                if has_cycle(step.id, visited, set()):
                    raise ValueError("Plán obsahuje cyklické závislosti")
    
    def _display_plan(self):
        """Zobrazí plán v čitelném formátu."""
        RichPrinter.info("✅ Plán vytvořen:")
        total_estimated = sum(s.estimated_tokens for s in self.steps)
        
        for step in self.steps:
            deps_str = ""
            if step.dependencies:
                deps_str = f" [dim](závisí na: {', '.join(map(str, step.dependencies))})[/dim]"
            
            RichPrinter.info(
                f"   [bold]{step.id}.[/bold] {step.description} "
                f"[dim]({step.estimated_tokens} tokens){deps_str}[/dim]"
            )
        
        RichPrinter.info(f"   [dim]Celkem kroků: {len(self.steps)} | "
                        f"Odhadované tokeny: {total_estimated}[/dim]")
    
    def get_next_step(self) -> Optional[PlanStep]:
        """
        Vrátí další krok k provedení (respektuje závislosti).
        
        Returns:
            PlanStep nebo None pokud žádný dostupný krok
        """
        for step in self.steps:
            if step.status == "pending":
                # Zkontroluj zda jsou splněny závislosti
                if self._are_dependencies_met(step):
                    return step
        
        return None  # Žádný dostupný krok
    
    def _are_dependencies_met(self, step: PlanStep) -> bool:
        """
        Zkontroluje zda jsou splněny všechny závislosti kroku.
        
        Args:
            step: Krok k ověření
        
        Returns:
            True pokud všechny závislosti jsou completed
        """
        for dep_id in step.dependencies:
            dep_step = next((s for s in self.steps if s.id == dep_id), None)
            if dep_step and dep_step.status != "completed":
                return False
        return True
    
    def mark_step_in_progress(self, step_id: int):
        """Označí krok jako probíhající."""
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "in_progress"
            RichPrinter.info(f"▶️  Krok {step_id}: {step.description}")
    
    def mark_step_completed(self, step_id: int, result: str, tokens_used: int):
        """
        Označí krok jako dokončený.
        
        Args:
            step_id: ID kroku
            result: Výsledek provedení (stdout/odpověď)
            tokens_used: Počet spotřebovaných tokenů
        """
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "completed"
            step.result = result
            step.actual_tokens = tokens_used
            RichPrinter.info(
                f"✅ Krok {step_id} dokončen "
                f"[dim]({tokens_used} tokens, "
                f"odhad: {step.estimated_tokens})[/dim]"
            )
    
    def mark_step_failed(self, step_id: int, error: str):
        """
        Označí krok jako selhavší.
        
        Args:
            step_id: ID kroku
            error: Chybová hláška
        """
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "failed"
            step.error = error
            RichPrinter.error(f"❌ Krok {step_id} selhal: {error}")
    
    def mark_step_skipped(self, step_id: int, reason: str):
        """
        Označí krok jako přeskočený.
        
        Args:
            step_id: ID kroku
            reason: Důvod přeskočení
        """
        step = self._get_step_by_id(step_id)
        if step:
            step.status = "skipped"
            RichPrinter.info(f"⏭️  Krok {step_id} přeskočen: {reason}")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Vrátí statistiky pokroku.
        
        Returns:
            {
                "total_steps": int,
                "completed": int,
                "failed": int,
                "in_progress": int,
                "pending": int,
                "progress_percent": float
            }
        """
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == "completed")
        failed = sum(1 for s in self.steps if s.status == "failed")
        in_progress = sum(1 for s in self.steps if s.status == "in_progress")
        pending = sum(1 for s in self.steps if s.status == "pending")
        
        progress_percent = (completed / total * 100) if total > 0 else 0
        
        return {
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "skipped": sum(1 for s in self.steps if s.status == "skipped"),
            "progress_percent": progress_percent
        }
    
    def _get_step_by_id(self, step_id: int) -> Optional[PlanStep]:
        """Najde krok podle ID."""
        return next((s for s in self.steps if s.id == step_id), None)
    
    def is_plan_complete(self) -> bool:
        """
        True pokud jsou všechny kroky dokončeny nebo přeskočeny.
        
        Returns:
            True pokud plán je kompletní (všechny kroky completed/skipped)
        """
        return all(s.status in ["completed", "skipped"] for s in self.steps)
    
    def has_failures(self) -> bool:
        """True pokud nějaký krok selhal."""
        return any(s.status == "failed" for s in self.steps)
    
    def get_failed_steps(self) -> List[PlanStep]:
        """Vrátí seznam selhavších kroků."""
        return [s for s in self.steps if s.status == "failed"]
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serializuje plán do JSON-friendly formátu.
        
        Returns:
            Dictionary pro uložení do state_data
        """
        return {
            "steps": [step.to_dict() for step in self.steps],
            "current_step_index": self.current_step_index,
            "plan_created_at": self.plan_created_at
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any], llm_manager) -> 'PlanManager':
        """
        Obnoví PlanManager ze serializované podoby.
        
        Args:
            data: Serializovaná data (z serialize())
            llm_manager: Instance LLMManager
        
        Returns:
            Obnovený PlanManager
        """
        pm = cls(llm_manager)
        pm.steps = [PlanStep.from_dict(s) for s in data["steps"]]
        pm.current_step_index = data.get("current_step_index", 0)
        pm.plan_created_at = data.get("plan_created_at")
        return pm
    
    def __repr__(self) -> str:
        """String reprezentace pro debugging."""
        progress = self.get_progress()
        return (
            f"PlanManager(steps={len(self.steps)}, "
            f"completed={progress['completed']}, "
            f"failed={progress['failed']})"
        )
