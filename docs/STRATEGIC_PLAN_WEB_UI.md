# Strategický Plán Implementace Webového UI

**Autor:** Jules (AI Agent)
**Datum:** 2025-10-07
**Verze:** 1.1

## 1. Východiska a Cíle

Tento dokument navazuje na diskuzi a analýzu shrnutou v `docs/ANALYZA_GITHUB_PROJEKTU.md`. Jeho cílem je definovat konkrétní, fázovaný plán pro implementaci moderního webového uživatelského rozhraní (Web UI/UX) pro projekt Nomád/Sophia.

**Hlavní strategické rozhodnutí:** Místo vývoje vlastního UI od nuly bude jako základ použit a adaptován existující open-source projekt **`open-webui`**. Tento přístup dramaticky urychlí vývoj, zajistí vysokou kvalitu a umožní nám soustředit se na klíčovou integrační logiku.

**Klíčové cíle:**
- Nahradit nebo doplnit stávající Textové UI (TUI) plnohodnotným webovým rozhraním.
- Zajistit stabilitu a nenarušit stávající jádro agenta (`JulesOrchestrator`).
- Implementovat koncept "Módů" pro zvýšení specializace a efektivity agenta.
- Vytvořit architekturu, která je od počátku připravena na budoucí integraci pokročilých nástrojů (terminál, IDE, vizualizace prohlížeče).

---

## 2. Navrhovaná Architektura

Nová architektura integruje `open-webui` se stávajícím jádrem "Nomad" pomocí propojovacího mostu (`NomadBridgeApi`).

```
+-----------------+      (HTTP/WS Request)    +------------------+      (Internal Call)      +----------------------+
|                 | ------------------------> |                  | -------------------------> |                      |
|  open-webui     |                           |  NomadBridgeApi  |                           |  JulesOrchestrator   |
|  (Svelte)       |      (WS Response)        |  (FastAPI)       |      (Callback/Queue)     |  (core/orchestrator) |
|                 | <------------------------ |                  | <------------------------- |                      |
+-----------------+                           +------------------+                           +----------------------+
```

---

## 3. Fázovaný Plán Implementace

### Fáze 1: Příprava a Integrace `open-webui`

1.  **Fork a začlenění `open-webui` jako submodulu.**
    *   **Akce:** Forknout repozitář `open-webui`. Přidat tento fork do našeho hlavního repozitáře jako git submodul do adresáře `web/ui/`.
    *   **Ověření:** Upravit `docker-compose.yml` tak, aby spouštěl `open-webui` jako samostatnou službu.

### Fáze 2: Vytvoření Propojovacího Mostu (API Adapter)

2.  **Návrh a implementace `NomadBridgeApi`.**
    *   **Akce:** Vytvořit `web/api/bridge.py` s FastAPI aplikací.
    *   **Endpointy:** `POST /chat` pro vstupy, `WS /stream` pro asynchronní výstupy (odpovědi, logy, stavy).

3.  **Adaptace `JulesOrchestrator` a `RichPrinter`.**
    *   **Akce:** Upravit jádro agenta, aby umělo komunikovat s novou API a posílat zprávy přes WebSocket.

### Fáze 3: Úprava Frontendu a Implementace "Módů"

4.  **Úprava `open-webui` frontendu (Svelte).**
    *   **Akce:** Upravit Svelte kód, aby komunikoval s `NomadBridgeApi`. Přidat komponenty pro vizualizaci stavu, plánu a logů.

5.  **Implementace systému "Módů".**
    *   **Akce:** Vytvořit v `core/` mechanismus pro správu "Módů" (např. `DeveloperMode`, `ResearchMode`). Přidat do UI prvek pro jejich přepínání.

---

## 4. Pokročilé Funkce a Rozšíření (Vize)

Základní webové UI je pouze začátek. Navržená architektura umožňuje postupnou integraci pokročilých funkcí, které z rozhraní udělají komplexní vývojové a monitorovací prostředí.

### 4.1 Integrovaný Terminál
- **Technologie:** `xterm.js` ve frontendu, streamování dat z PTY (pseudo-terminálu) na backendu přes WebSocket.
- **Funkce:** Poskytne živý, interaktivní pohled do shellu, ve kterém agent pracuje.

### 4.2 Plnohodnotné Vývojové Prostředí (IDE)
- **Strategie:** Integrace `code-server` jako preferované, robustní řešení.
- **Implementace:** Spustit `code-server` jako samostatný kontejner v `docker-compose.yml`. Jeho rozhraní vložit přímo do `open-webui` (např. pomocí `<iframe>`).
- **Funkce:** Uživatel získá přístup k plnohodnotnému VS Code v prohlížeči s přístupem k souborovému systému projektu.

### 4.3 Vizuální Zpětná Vazba z Prohlížeče
- **Technologie:** Playwright v "headed" režimu na serveru s využitím virtuálního displeje (Xvfb).
- **Implementace:** Streamování snímků obrazovky nebo videa z virtuálního prohlížeče agenta přes WebSocket do UI.
- **Funkce:** Poskytne absolutní transparentnost tím, že uživatel uvidí přesně to, co "vidí" a dělá agent ve webovém prohlížeči.

---

## 5. Závěr

Tento plán představuje komplexní, ale realistickou cestu k vybudování špičkového webového rozhraní. Kombinací adaptace `open-webui`, vytvořením robustního API mostu a postupnou integrací pokročilých funkcí vznikne nástroj, který výrazně posune možnosti interakce, vývoje a monitorování agenta Sophia/Nomád.