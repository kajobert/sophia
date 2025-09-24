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

### 3. Spuštění Pomocí Docker Compose (nebo lokálně bez Dockeru)

Nyní, když máte vše připraveno, spusťte celý ekosystém jediným příkazem (Docker doporučeno):

```bash
docker compose up --build
```

Pokud preferujete běh bez Dockeru, spusťte backend lokálně pomocí Uvicorn (FastAPI):

```bash
# Spusťte z kořene repozitáře
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Ověření Funkčnosti

Po úspěšném spuštění bude projekt dostupný na následujících adresách:

- **Frontend (Webové Rozhraní):** `http://localhost:3000` (pokud frontend běží)
- **Backend (API):** `http://localhost:8000/docs` (interaktivní dokumentace API)

Interakce s inteligencí nyní probíhá přes kognitivní pipeline (Reptilian -> Mammalian -> Neocortex). Pro lokální experimenty můžete použít `interactive_session.py` k otevření jednoduché CLI relace s těmito vrstvami.

Gratulujeme, právě jste úspěšně spustili Sophii!

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
