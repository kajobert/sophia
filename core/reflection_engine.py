"""
Reflection Engine - Učení z chyb a adaptivní rozhodování.

Tento modul analyzuje selhání kroků a navrhuje strategii pro recovery.
Používá LLM k deep analysis root cause a rozhoduje mezi:
- retry (zkus znovu)
- retry_modified (zkus s úpravami)
- replanning (přeplánuj celou misi)
- ask_user (potřebuji pomoc)
- skip_step (tento krok není kritický)

ARCHITEKTURA:
- ReflectionResult: Výstup reflexe s analýzou a doporučením
- ReflectionEngine: Provádění reflexe pomocí LLM
- Historie reflexí pro detekci opakujících se vzorů

POUŽITÍ:
    re = ReflectionEngine(llm_manager)
    
    # Po selhání kroku
    reflection = await re.reflect_on_failure(
        failed_step={"id": 3, "description": "..."},
        error_message="FileNotFoundError: file.txt",
        attempt_count=2,
        plan_context="..."
    )
    
    if reflection.suggested_action == "retry":
        # Zkus krok znovu
    elif reflection.suggested_action == "replanning":
        # Vytvoř nový plán

KLÍČOVÉ VLASTNOSTI:
- Root cause analysis (ne jen symptoms)
- Pattern detection (opakující se chyby)
- Confidence scoring (jak si je jistý)
- Historie pro kontextové rozhodování
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from core.rich_printer import RichPrinter
import json
import re


@dataclass
class ReflectionResult:
    """
    Výsledek reflexe po chybě/úspěchu.
    
    Attributes:
        analysis: Lidsky čitelná analýza co se stalo
        root_cause: Identifikovaná základní příčina (ne symptom)
        suggested_action: Doporučená akce ("retry", "retry_modified", "replanning", "ask_user", "skip_step")
        confidence: Jak si je systém jistý (0.0 - 1.0)
        modification_hint: Pokud action=retry_modified, jak upravit krok
    """
    analysis: str
    root_cause: str
    suggested_action: str
    confidence: float
    modification_hint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konverze na dictionary."""
        return {
            "analysis": self.analysis,
            "root_cause": self.root_cause,
            "suggested_action": self.suggested_action,
            "confidence": self.confidence,
            "modification_hint": self.modification_hint
        }


class ReflectionEngine:
    """
    Provádí reflexi po chybách a adaptuje strategii.
    
    ARCHITEKTONICKÉ ROZHODNUTÍ:
    - Reflexe používá "powerful" LLM model (strategické myšlení)
    - Historie reflexí je omezena na posledních 10 (pro kontext ale ne přehlcení)
    - Confidence < 0.5 = doporučení ask_user
    """
    
    def __init__(self, llm_manager):
        """
        Inicializace ReflectionEngine.
        
        Args:
            llm_manager: Instance LLMManager pro komunikaci s LLM
        """
        self.llm_manager = llm_manager
        self.reflection_history: List[Dict[str, Any]] = []
        self.max_history_size = 10
    
    async def reflect_on_failure(
        self, 
        failed_step: Dict[str, Any],
        error_message: str,
        attempt_count: int,
        plan_context: str = ""
    ) -> ReflectionResult:
        """
        Analyzuje selhání kroku a navrhne další akci.
        
        Args:
            failed_step: Informace o selhaném kroku ({"id": 1, "description": "..."})
            error_message: Chybová hláška/výstup
            attempt_count: Kolikátý pokus to byl (1 = první selhání)
            plan_context: Kontext celkového plánu (volitelné)
        
        Returns:
            ReflectionResult s analýzou a doporučením
        """
        RichPrinter.warning(f"🤔 Reflexe selhání (pokus #{attempt_count})...")
        
        # Sestavení promptu pro LLM
        reflection_prompt = self._build_reflection_prompt(
            failed_step, error_message, attempt_count, plan_context
        )
        
        # Zavolej LLM
        try:
            model = self.llm_manager.get_llm("powerful")
        except (ValueError, FileNotFoundError):
            RichPrinter.warning("⚠️  'powerful' model nedostupný, používám default")
            model = self.llm_manager.get_llm(self.llm_manager.default_llm_name)
        
        response, _ = await model.generate_content_async(reflection_prompt)
        
        # Parse odpověď
        reflection_data = self._parse_reflection_response(response)
        
        if not reflection_data:
            # Fallback pokud parsing selže
            RichPrinter.error("❌ Nepodařilo se zparsovat reflexi, používám fallback")
            return self._fallback_reflection(attempt_count)
        
        # Vytvoř ReflectionResult
        result = ReflectionResult(
            analysis=reflection_data.get("analysis", "No analysis provided"),
            root_cause=reflection_data.get("root_cause", "Unknown"),
            suggested_action=reflection_data.get("suggested_action", "ask_user"),
            confidence=reflection_data.get("confidence", 0.5),
            modification_hint=reflection_data.get("modification_hint")
        )
        
        # Zaznamenej do historie
        self._record_reflection(failed_step, error_message, result)
        
        # Zobraz výsledek
        self._display_reflection(result)
        
        return result
    
    def _build_reflection_prompt(
        self,
        failed_step: Dict[str, Any],
        error_message: str,
        attempt_count: int,
        plan_context: str
    ) -> str:
        """Sestaví prompt pro LLM reflexi."""
        
        # Formátuj historii pro kontext
        history_str = self._format_reflection_history()
        
        return f"""Jsi analytik chyb AI agenta. Analyzuj následující selhání a navrhni nejlepší další krok.

DŮLEŽITÉ: Hledej SKUTEČNOU PŘÍČINU (root cause), ne jen symptom!

SELHAVŠÍ KROK:
ID: {failed_step.get('id', 'N/A')}
Popis: {failed_step.get('description', 'N/A')}

CHYBOVÁ HLÁŠKA:
{error_message}

POKUS Č.: {attempt_count}

KONTEXT PLÁNU:
{plan_context if plan_context else "Žádný kontext plánu."}

HISTORIE PŘEDCHOZÍCH REFLEXÍ:
{history_str}

TVŮJ ÚKOL:
1. Analyzuj CO SE SKUTEČNĚ STALO (ne jen co říká error message)
2. Identifikuj ROOT CAUSE (základní příčinu)
3. Navrhni KONKRÉTNÍ akci

MOŽNÉ AKCE:
- "retry": Zkus stejný krok znovu (pokud je chyba přechodná, např. network timeout)
- "retry_modified": Zkus modifikovanou verzi (uprav parametry/přístup)
- "replanning": Plán je špatný nebo nerealistický, je třeba přeplánovat
- "ask_user": Potřebuji pomoc nebo upřesnění od uživatele (nejasný úkol, chybějící info)
- "skip_step": Tento krok není kritický pro splnění mise, lze přeskočit

HEURISTIKY:
- Pokud stejná chyba opakovaně (attempt > 2): zvažuj "replanning" nebo "ask_user"
- Pokud FileNotFoundError/PermissionError: může být "retry_modified" s jinou cestou
- Pokud SyntaxError/TypeError: pravděpodobně "replanning" (logická chyba)
- Pokud NetworkError/Timeout: "retry" (přechodná chyba)
- Pokud ValidationError: "ask_user" (nejasné požadavky)

FORMÁT ODPOVĚDI (POUZE JSON):
{{
  "analysis": "Stručná analýza co se stalo (2-3 věty)",
  "root_cause": "Skutečná příčina (ne symptom!) - např. 'Chybějící závislost' ne jen 'ImportError'",
  "suggested_action": "retry|retry_modified|replanning|ask_user|skip_step",
  "confidence": 0.8,
  "modification_hint": "Pokud action=retry_modified, napiš JAK upravit krok. Jinak null."
}}

PŘÍKLAD:
{{
  "analysis": "Krok selhal kvůli FileNotFoundError. Hledaný soubor 'config.yaml' neexistuje.",
  "root_cause": "Soubor očekáván v nesprávné cestě - pravděpodobně chybí prefix PROJECT_ROOT/",
  "suggested_action": "retry_modified",
  "confidence": 0.85,
  "modification_hint": "Změň cestu z 'config.yaml' na 'PROJECT_ROOT/config/config.yaml'"
}}
"""
    
    def _parse_reflection_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON reflexe z LLM odpovědi.
        
        Args:
            response: Raw response z LLM
        
        Returns:
            Dictionary nebo None pokud parsing selže
        """
        # Pokus 1: JSON v markdown code blocku
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
        
        # Pokus 3: Zkus celou odpověď
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return None
    
    def _fallback_reflection(self, attempt_count: int) -> ReflectionResult:
        """
        Fallback reflexe pokud LLM parsing selže.
        
        Jednoduchá heuristika:
        - 1. pokus: retry
        - 2. pokus: retry
        - 3+ pokus: ask_user
        """
        if attempt_count <= 2:
            return ReflectionResult(
                analysis="LLM reflexe selhala. Používám fallback: zkus znovu.",
                root_cause="Unknown (LLM parsing failed)",
                suggested_action="retry",
                confidence=0.3
            )
        else:
            return ReflectionResult(
                analysis="Opakované selhání. Fallback: požádat uživatele o pomoc.",
                root_cause="Unknown (LLM parsing failed)",
                suggested_action="ask_user",
                confidence=0.3
            )
    
    def _record_reflection(
        self,
        failed_step: Dict[str, Any],
        error_message: str,
        result: ReflectionResult
    ):
        """Zaznamenej reflexi do historie."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "step_id": failed_step.get("id"),
            "step_description": failed_step.get("description"),
            "error": error_message[:200],  # Omez délku
            "result": result.to_dict()
        }
        
        self.reflection_history.append(record)
        
        # Omez velikost historie
        if len(self.reflection_history) > self.max_history_size:
            self.reflection_history.pop(0)
    
    def _format_reflection_history(self) -> str:
        """Formátuje historii reflexí pro kontext v promptu."""
        if not self.reflection_history:
            return "Žádné předchozí reflexe."
        
        # Zobraz posledních 3
        recent = self.reflection_history[-3:]
        formatted = []
        for i, ref in enumerate(recent, 1):
            formatted.append(
                f"{i}. Krok {ref.get('step_id', '?')}: "
                f"{ref['error'][:80]}... → "
                f"Akce: {ref['result']['suggested_action']} "
                f"(confidence: {ref['result']['confidence']:.0%})"
            )
        return "\n".join(formatted)
    
    def _display_reflection(self, result: ReflectionResult):
        """Zobraz výsledek reflexe."""
        RichPrinter.info(f"💡 Analýza: {result.analysis}")
        RichPrinter.info(f"🎯 Příčina: {result.root_cause}")
        RichPrinter.info(
            f"➡️  Doporučení: [bold]{result.suggested_action}[/bold] "
            f"(confidence: {result.confidence:.0%})"
        )
        
        if result.modification_hint:
            RichPrinter.info(f"💬 Hint: {result.modification_hint}")
    
    async def reflect_on_success(self, completed_step: Dict[str, Any]):
        """
        Reflexe po úspěšném kroku (pro budoucí učení).
        
        Args:
            completed_step: Informace o dokončeném kroku
        """
        # Jednodušší - jen zaznamenej do historie
        record = {
            "timestamp": datetime.now().isoformat(),
            "step_id": completed_step.get("id"),
            "step_description": completed_step.get("description"),
            "result": {"status": "success"}
        }
        
        self.reflection_history.append(record)
        
        # Omez velikost
        if len(self.reflection_history) > self.max_history_size:
            self.reflection_history.pop(0)
    
    def get_failure_patterns(self) -> Dict[str, int]:
        """
        Analyzuje opakující se vzory selhání.
        
        Returns:
            Dictionary {root_cause: počet_výskytů}
        """
        patterns = {}
        for reflection in self.reflection_history:
            if "result" in reflection and "root_cause" in reflection["result"]:
                root_cause = reflection["result"]["root_cause"]
                patterns[root_cause] = patterns.get(root_cause, 0) + 1
        return patterns
    
    def get_most_common_failure(self) -> Optional[str]:
        """Vrátí nejčastější root cause nebo None."""
        patterns = self.get_failure_patterns()
        if not patterns:
            return None
        return max(patterns, key=patterns.get)
    
    def clear_history(self):
        """Vyčisti historii reflexí (např. při nové misi)."""
        self.reflection_history = []
