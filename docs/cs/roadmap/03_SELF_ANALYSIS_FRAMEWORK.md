# Roadmapa 03: Rámec pro sebeanalýzu

**Stav:** DOKONČENO

**Cíl fáze:** Vyvinout schopnost Sofie pro introspekci. Tato fáze zahrnovala vytvoření sady kognitivních pluginů, které jí umožňují číst, rozumět a uvažovat o své vlastní struktuře, kódu a dokumentaci. Toto byl kritický krok před tím, než lze uvažovat o skutečné autonomii.

---

### Klíčové cíle:

1.  **Plugin pro porozumění kódu (`cognitive_code_reader`):**
    *   **Stav:** DOKONČENO
    *   **Účel:** Umožnit Sofii číst a vytvářet si mentální model svého vlastního zdrojového kódu.
    *   **Klíčové schopnosti:** `analyze_codebase`, `get_class_definition`, `get_function_signature`, `list_plugins`.

2.  **Plugin pro porozumění dokumentaci (`cognitive_doc_reader`):**
    *   **Stav:** DOKONČENO
    *   **Účel:** Umožnit Sofii číst a rozumět své vlastní dokumentaci a proměnit ji v akční zdroj pravdy pro své chování.
    *   **Klíčové schopnosti:** `read_document`, `find_guideline`, `get_architectural_overview`.

3.  **Plugin pro analýzu závislostí (`cognitive_dependency_analyzer`):**
    *   **Stav:** DOKONČENO
    *   **Účel:** Dát Sofii schopnost rozumět svým softwarovým závislostem.
    *   **Klíčové schopnosti:** `list_dependencies`, `check_dependency_version`.

4.  **Plugin pro historickou analýzu (`cognitive_historian`):**
    *   **Stav:** DOKONČENO
    *   **Účel:** Umožnit Sofii učit se z historie projektu analýzou `WORKLOG.md` a dalších historických záznamů.
    *   **Klíčové schopnosti:** `review_past_missions`, `identify_past_failures`, `summarize_agent_performance`.

---

**Kritéria úspěchu:** Sofie může být dotázána: "Jaké jsou podle tvé dokumentace povinné kroky pro vytvoření nového pluginu a existují nějaké existující pluginy, které plní podobnou funkci?" Měla by být schopna na tuto otázku správně odpovědět pomocí těchto nástrojů pro sebeanalýzu.

**Výsledek:** Všechny cíle této fáze byly splněny. Systém je nyní připraven přejít k další fázi: Autonomní operace.
