# Sophia V4 - Docker Compose

Tento soubor spouští celý ekosystém Sophia v oddělených kontejnerech:
- backend (FastAPI, port 8000)
- frontend (React, port 3000)
- databáze (PostgreSQL, port 5432)

## Spuštění

1. Ujisti se, že máš nainstalovaný Docker a Docker Compose.
2. V kořenovém adresáři projektu spusť:

   docker compose up --build

3. Frontend bude dostupný na http://localhost:3000
   Backend API na http://localhost:8000
   Databáze na portu 5432

## Vývoj
- Kód je mountován jako volume, změny v kódu se ihned projeví (hot reload).
- Pro frontend je nastaven CHOKIDAR_USEPOLLING=true pro spolehlivý hot reload v Dockeru.

## Produkce
- Pro produkční build frontendu použij `npm run build` a nasazení přes reverse proxy (Nginx/Caddy).
- Backend lze spustit bez --reload.

## Debugging
- Logy všech služeb jsou dostupné přes Docker Compose.
- Pokud je port obsazený, změň jej v docker-compose.yml.

---

Pro více informací viz dokumentaci projektu Sophia.
