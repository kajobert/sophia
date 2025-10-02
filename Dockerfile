# syntax=docker/dockerfile:1
FROM python:3.12-slim

# 1. Nastavení pracovního adresáře
WORKDIR /app

# 2. Instalace uv pro správu závislostí
RUN pip install uv

# 3. Kopírování a instalace závislostí
# Kopírujeme pouze soubor se závislostmi pro efektivní využití Docker cache
COPY requirements.in ./
RUN uv pip install --system --no-cache-dir -r requirements.in

# 4. Kopírování celého zdrojového kódu aplikace
COPY . .

# 5. Vystavení portu, na kterém aplikace poběží
EXPOSE 8000

# 6. Spouštěcí příkaz
# Spustí guardian skript, který se stará o TUI aplikaci.
CMD ["python", "guardian/runner.py"]
