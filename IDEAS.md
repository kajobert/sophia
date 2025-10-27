# IDEAS.md

## Nápad: Robustní Tool-Calling pomocí "Validation & Repair Loop" místo Finetuningu

**Problém:**
Potřebujeme, aby AI agent (Sophia) volal nástroje pomocí JSONu se 100% spolehlivostí. Finetuning modelů je drahý, časově náročný a stejně nikdy nezaručí 100% úspěšnost.

**Řešení: "Validation & Repair Loop" (Validační a Opravná Smyčka)**
Místo snahy donutit model, aby nikdy neudělal chybu, budeme aktivně předpokládat, že chybu udělá, a budeme mít proces na její okamžitou opravu.

**Platforma:**
Použít OpenRouter pro přístup k nejlepším modelům v poměru cena/výkon (např. Claude 3 Haiku, Mixtral, Llama 3 70B) místo drahého placení za prémiové modely (Gemini Pro, GPT-4o).

**Technický postup (Python):**

1.  **Definice Schématu:** Použít knihovnu **Pydantic** k definování přesné datové struktury (schématu) JSONu, který od AI očekáváme pro volání nástroje.
2.  **První pokus (Try):** Požádáme levný model (např. Claude 3 Haiku) o vygenerování JSONu pro volání nástroje.
3.  **Validace (Except):** Okamžitě se pokusíme naparsovat odpověď modelu pomocí našeho Pydantic schématu v `try...except` bloku.
4.  **Opravná Smyčka (Repair Loop):**
    * Pokud `ValidationError` selže (`except ValidationError as e:`):
    * Vezmeme původní rozbitý JSON *a* detailní chybovou hlášku z Pydanticu (`e.errors()`).
    * Pošleme obojí zpět tomu samému (nebo jinému levnému) modelu.
    * Prompt pro opravu: `"POZOR: JSON selhal při validaci. Chyby: [zde vložit e.errors()]. Oprav JSON. Neomlouvej se, pošli jen opravený kód."`
5.  **Výsledek:** Tento proces je levnější (využívá levné modely) a mnohem robustnější (zachytí a opraví i chyby, které by udělal drahý finetunovaný model). Cílem není 100% úspěšnost modelu, ale 99.9%+ úspěšnost celého systému.
   
