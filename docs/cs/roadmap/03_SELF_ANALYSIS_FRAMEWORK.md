# Roadmapa 03: Rámec pro Sebe-Analýzu

**Cíl Fáze:** Rozvinout schopnost Sophie pro introspekci. Tato fáze zahrnuje vytvoření sady kognitivních pluginů, které jí umožní číst, chápat a uvažovat o své vlastní struktuře, kódu a dokumentaci. Toto je kritický krok před tím, než bude možné uvažovat o skutečné autonomii.

Detailní implementační plán pro tuto fázi bude vytvořen po úspěšném dokončení fáze Integrace Nástrojů.

---

### Klíčové Cíle:

1.  **Plugin pro Porozumění Kódu (`cognitive_code_reader`):**
    *   **Účel:** Umožnit Sophii číst a vytvářet si mentální model svého vlastního zdrojového kódu.
    *   **Základní Schopnosti:** `analyze_codebase`, `get_class_definition`, `get_function_signature`, `list_plugins`.

2.  **Plugin pro Porozumění Dokumentaci (`cognitive_doc_reader`):**
    *   **Účel:** Umožnit Sophii číst a chápat svou vlastní dokumentaci a proměnit ji v akční zdroj pravdy pro své chování.
    *   **Základní Schopnosti:** `read_document`, `find_guideline`, `get_architectural_overview`.

3.  **Plugin pro Analýzu Závislostí (`cognitive_dependency_analyzer`):**
    *   **Účel:** Poskytnout Sophii schopnost rozumět svým softwarovým závislostem.
    *   **Základní Schopnosti:** `list_dependencies`, `check_dependency_version`.

4.  **Plugin pro Historickou Analýzu (`cognitive_historian`):**
    *   **Účel:** Umožnit Sophii učit se z historie projektu analýzou `WORKLOG.md` a dalších historických záznamů.
    *   **Základní Schopnosti:** `review_past_missions`, `identify_past_failures`, `summarize_agent_performance`.

---

**Kritéria Úspěchu:** Sophii lze položit otázku: "Jaké jsou podle tvé dokumentace povinné kroky pro vytvoření nového pluginu a existují nějaké existující pluginy, které vykonávají podobnou funkci?" Měla by být schopna na tuto otázku správně odpovědět pomocí těchto nástrojů pro sebe-analýzu.
