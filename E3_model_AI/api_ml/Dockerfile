# Utiliser une image Python optimisée
FROM python:3.9-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Copier tous les fichiers dans le conteneur
COPY api_ml/ ./api_ml/
COPY model_ml/ ./model_ml/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 8000 pour FastAPI
EXPOSE 8000

# Commande pour démarrer l'API avec Uvicorn
CMD ["uvicorn", "api_ml.main_api_ml:app", "--host", "0.0.0.0", "--port", "8000"]
