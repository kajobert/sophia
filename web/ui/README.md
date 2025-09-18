# Sophia Web UI

Tento adresář obsahuje frontendovou SPA aplikaci (React) pro projekt Sophia.

## Spuštění vývojového serveru

1. Otevři terminál v adresáři `web/ui/`.
2. Spusť:

   npm install
   npm run start

Výchozí port je 3000. Aplikace bude dostupná na http://localhost:3000

## Build

    npm run build

Vytvoří produkční build v adresáři `dist/`.

## Testování

    npm test

Spustí integrační testy pomocí Jest a Testing Library. Testy ověřují základní funkčnost UI (menu, chat, interakce).

## Struktura
- `public/` – statické soubory (index.html, manifest.json)
- `src/` – zdrojové kódy React aplikace
- `src/components/` – jednotlivé UI komponenty (Chat, Login, Upload, ...)
- `src/__tests__/` – integrační testy UI

----

Pro více informací viz dokumentace projektu Sophia.
