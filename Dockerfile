# syntax=docker/dockerfile:1
FROM python:3.12-slim

# 1. Nastavení pracovního adresáře
WORKDIR /app

# 2. Instalace systémových závislostí
# Potřebujeme 'git' pro guardian a 'libncursesw6' pro běh Textual TUI.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libncursesw6 \
    && rm -rf /var/lib/apt/lists/*

# 3. Instalace uv pro správu závislostí
RUN pip install uv

# 4. Kopírování a instalace Python závislostí
# Tento krok je stále užitečný pro cachování.
# Pokud se 'requirements.in' nezmění, Docker použije cache.
COPY requirements.in ./
RUN uv pip install --system --no-cache-dir -r requirements.in

# 5. Spouštěcí příkaz
# CMD sice definujeme zde, ale klíčové bude nastavení v docker-compose.
CMD ["python", "guardian/runner.py"]