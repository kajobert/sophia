# 🚀 Quickstart: Spuštění Sophie

Tento návod vás provede nejrychlejším způsobem, jak zprovoznit projekt Sophia na vašem lokálním stroji pomocí Dockeru. Tento přístup je doporučený, protože zajišťuje, že všechny komponenty (backend, frontend, databáze) poběží v konzistentním a izolovaném prostředí.

## Předpoklady

-   Máte nainstalovaný [Docker](https://www.docker.com/products/docker-desktop/) a Docker Compose.
-   Máte základní znalosti práce s terminálem.

## Kroky ke Spuštění

### 1. Klonování Repozitáře

Nejprve si naklonujte tento repozitář na svůj lokální stroj:

```bash
git clone https://github.com/kajobert/sophia.git
cd sophia
```

### 2. Nastavení Konfigurace

Projekt vyžaduje API klíče pro připojení k jazykovým modelům. Tyto klíče se nastavují v souboru `.env`.

-   V kořenovém adresáři projektu najdete soubor `.env.example`. Zkopírujte ho a přejmenujte kopii na `.env`:

    ```bash
    cp .env.example .env
    ```

-   Otevřete soubor `.env` v textovém editoru a doplňte požadované API klíče. Bez nich nebude Sophia schopna komunikovat s LLM.

### 3. Spuštění Pomocí Docker Compose

Nyní, když máte vše připraveno, spusťte celý ekosystém jediným příkazem:

```bash
docker compose up --build
```

-   Příkaz `--build` zajistí, že se Docker obrazy vytvoří poprvé (nebo přebudují, pokud došlo ke změnám v `Dockerfile`).
-   Spuštění může chvíli trvat, Docker musí stáhnout a nainstalovat všechny závislosti.

### 4. Ověření Funkčnosti

Po úspěšném spuštění bude projekt dostupný na následujících adresách:

-   **Frontend (Webové Rozhraní):** `http://localhost:3000`
-   **Backend (API):** `http://localhost:8000/docs` (interaktivní dokumentace API)

Otevřete v prohlížeči `http://localhost:3000` a měli byste vidět hlavní stránku webového rozhraní Sophie.

Gratulujeme, právě jste úspěšně spustili Sophii!

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
