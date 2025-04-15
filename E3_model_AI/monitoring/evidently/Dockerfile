FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Exposer le port pour Evidently
EXPOSE 8001

CMD ["python", "/app/evidently_prometheus.py"]