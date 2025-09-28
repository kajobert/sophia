# 🗺️ Plán Vývoje Projektu Sophia (Roadmap)

**Verze:** 1.0
**Datum:** 2025-09-28

Tento dokument popisuje plánované kroky a budoucí směřování projektu Sophia, se zaměřením na jádro "Nomad".

---

## Krátkodobé Cíle (Next Up)

- **[ ] Vylepšení Offline Režimu:**
  - Prozkoumat a implementovat možnost využití lokálního LLM (např. Ollama, Llama.cpp), když není k dispozici API klíč pro Gemini.
  - Cílem je poskytnout základní funkčnost a schopnost plnit jednodušší úkoly i bez přístupu k externím službám.

- **[ ] Integrace Kognitivních Funkcí:**
  - Postupně integrovat a refaktorovat moduly z původní složky `integrace/` do nového jádra Nomad.
  - Prioritou je modul pro pokročilou správu paměti (`AdvancedMemory`).

- **[ ] Rozšíření Testovací Sady:**
  - Vytvořit sadu jednotkových a integračních testů pro novou architekturu (Orchestrátor, MCP servery, TUI).
  - Cílem je zajistit stabilitu a předejít regresím.

## Dlouhodobá Vize

- **[ ] Plná Autonomie Agenta:** Rozšířit schopnosti agenta tak, aby dokázal samostatně analyzovat, plánovat a řešit komplexní, více-krokové softwarové projekty.
- **[ ] Webové Rozhraní:** Nahradit nebo doplnit TUI moderním webovým rozhraním pro lepší vizualizaci a interakci.
- **[ ] Multi-agentní Spolupráce:** Vytvořit architekturu, která umožní spolupráci více agentů na jednom úkolu.