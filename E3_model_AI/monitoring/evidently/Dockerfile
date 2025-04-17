FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances
COPY monitoring/evidently/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les fichiers nécessaires (script, CSV, etc.)
COPY monitoring/evidently/. .

# Exposer le port Prometheus
EXPOSE 8001

# Lancer le script
CMD ["python3", "-u", "evidently_prometheus.py"]
