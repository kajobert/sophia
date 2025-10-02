# syntax=docker/dockerfile:1
FROM python:3.12-slim

# 1. Nastavení pracovního adresáře
WORKDIR /app

# 2. Instalace systémových závislostí (git pro guardian a ncurses pro Textual)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libncurses-dev

# 3. Instalace uv pro správu závislostí
RUN pip install uv

# 4. Kopírování a instalace závislostí
COPY requirements.in ./
RUN uv pip install --system --no-cache-dir -r requirements.in

# 5. Kopírování celého zdrojového kódu aplikace
COPY . .

# 6. Spouštěcí příkaz
# Spustí guardian skript, který se stará o TUI aplikaci.
CMD ["python", "guardian/runner.py"]