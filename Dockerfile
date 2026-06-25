# ============================================================
# BNC-OTAKU — Dockerfile (Python 3.11 + Playwright)
# ============================================================

FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer Chromium pour Playwright
RUN playwright install chromium

# Code applicatif
COPY . .

# Port d'exposition
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
