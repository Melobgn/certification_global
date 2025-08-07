FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Créer le dossier staticfiles si nécessaire
RUN mkdir -p /app/staticfiles



VOLUME /app/staticfiles


