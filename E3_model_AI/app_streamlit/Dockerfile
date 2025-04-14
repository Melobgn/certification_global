# Utiliser une image Python légère
FROM python:3.9-slim

# Installer dépendances système pour OpenCV/YOLO
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt /app/requirements.txt
COPY app_streamlit/ ./app_streamlit/
# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 8501 pour Streamlit
EXPOSE 8501

# Démarrer l'application Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]