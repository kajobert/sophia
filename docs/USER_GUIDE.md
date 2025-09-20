# 📘 Uživatelský Průvodce pro Projekt Sophia

Vítejte! Tento průvodce je určen pro vás, koncové uživatele, kteří chtějí komunikovat se Sophií a využívat její schopnosti prostřednictvím webového rozhraní.

Pokud jste zde poprvé a potřebujete pomoc se zprovozněním projektu, podívejte se prosím nejprve na **[🚀 QUICKSTART.md](../QUICKSTART.md)**.

## Co je Sophia?

Z uživatelského pohledu je Sophia inteligentní partnerka pro dialog. Můžete s ní vést běžnou konverzaci, zadávat jí úkoly, nebo se jí ptát na složité filosofické otázky. Jejím cílem je nejen odpovídat, ale také se z vašich interakcí učit a porozumět světu lépe.

## Přihlášení

Při první návštěvě webového rozhraní budete vyzváni k přihlášení.

-   **Přihlášení přes Google:** Klikněte na tlačítko pro přihlášení přes Google. Tím propojíte svůj účet a umožníte Sophii, aby si pamatovala vaše minulé konverzace a preference.

## Popis Rozhraní

Po přihlášení se vám zobrazí hlavní obrazovka, která je rozdělena do několika částí.

### Hlavní Menu (Levý Panel)

Na levé straně obrazovky naleznete hlavní menu, které slouží k navigaci mezi jednotlivými funkcemi aplikace:

-   **💬 Chat:** Hlavní okno pro konverzaci se Sophií.
-   **📂 Files (Soubory):** Zde budete moci nahrávat soubory, se kterými má Sophia pracovat (tato funkce je ve vývoji).
-   **👤 Profile (Profil):** Informace o vašem uživatelském účtu.
-   **⚙️ Settings (Nastavení):** Možnosti pro přizpůsobení chování aplikace.
-   **🔔 Notifications (Notifikace):** Upozornění od systému.
-   **헬 Helpdesk:** Centrum nápovědy.

### Konverzační Okno (Chat)

Toto je srdce aplikace, kde probíhá veškerá komunikace.

1.  **Vstupní pole:** Do textového pole ve spodní části obrazovky napište svou zprávu, dotaz nebo úkol.
2.  **Odeslání:** Stiskněte Enter nebo klikněte na tlačítko pro odeslání.
3.  **Odpověď:** Vaše zpráva se zobrazí v okně chatu a Sophia po chvíli odpoví. Historie vaší konverzace zůstává viditelná, takže se můžete snadno vracet k předchozím tématům.

### Spouštění Úkolů (Task Runner)

Kromě běžného chatu můžete Sophii zadávat i komplexnější úkoly, které vyžadují plánování a provedení několika kroků. K tomu slouží záložka **"Task Runner"**.

1.  **Zadání úkolu:** V textovém poli popište, co má Sophia udělat. Buďte co nejkonkrétnější. Například: "Vytvoř v aktuálním adresáři soubor s názvem `test.txt` a napiš do něj 'Ahoj světe!'".
2.  **Spuštění:** Klikněte na tlačítko "Run Task".
3.  **Sledování průběhu:** Po odeslání úkolu se zobrazí jeho unikátní ID a pod ním uvidíte v reálném čase jednotlivé kroky, které Sophia provádí.
    -   ✔️ **Zelená fajfka** znamená, že krok proběhl úspěšně.
    -   ❌ **Červený křížek** značí, že došlo k chybě. Sophia se pokusí plán opravit a pokračovat.
4.  **Výsledek:** Po dokončení celého plánu se zobrazí finální zpráva o úspěchu či neúspěchu.

## Řešení Běžných Problémů

-   **Aplikace neodpovídá:** Ujistěte se, že všechny Docker kontejnery běží správně (viz `QUICKSTART.md`). Zkontrolujte logy v terminálu, kde jste spustili `docker compose up`.
-   **Chyba při přihlášení:** Ověřte, že máte správně nastavené API klíče v souboru `.env`.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
