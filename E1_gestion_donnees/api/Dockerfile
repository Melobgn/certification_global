# Image de base Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source de l'API
COPY api/ ./api/
COPY database/ ./database/

# Exposer le port
EXPOSE 8000

# Commande pour démarrer l'API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"] 