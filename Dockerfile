FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Chat-Help Assistant"
LABEL description="Serveur MCP pour assistant IA des étudiants en informatique"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_ENV=production

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ ./src/

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 chathelp && \
    chown -R chathelp:chathelp /app

USER chathelp

# Point d'entrée
CMD ["python", "-m", "src.server"]