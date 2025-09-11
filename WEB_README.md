# Přidání webového rozhraní k Sophii

## Backend (Flask API)
- `/web_api.py` spouští Flask server na portu 5000 a poskytuje endpoint `/api/chat` pro komunikaci s jádrem Sophia.
- Každý POST požadavek s JSON `{ "message": "..." }` vytvoří Task, spustí Crew a vrátí odpověď Sophie.

## Frontend
- `/webui.html` je jednoduchý moderní chat inspirovaný AI chatboty.
- Odesílá dotazy na `/api/chat` a zobrazuje odpovědi.

## Spuštění
1. Spusť backend:  
   `python web_api.py`
2. Otevři `webui.html` v prohlížeči (např. dvojklikem nebo přes VS Code Live Server).

---

- Pokud chceš frontend zpřístupnit i vzdáleně, použij např. [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) nebo nastav CORS dle potřeby.
- Pro produkci doporučuji nasadit Flask přes WSGI server (např. gunicorn).
