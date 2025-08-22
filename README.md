# Certification Global

Plateforme complète pour la détection d’armes dans des catalogues e‑commerce, de la collecte de données jusqu’à l’application web d’annotation et de monitoring.

## Structure du dépôt

| Dossier | Rôle principal |
|---------|----------------|
| **E1_gestion_donnees/** | Collecte et gestion des données (Scrapy, FastAPI, SQLite). Contient l’API d’accès aux produits, les spiders et la base de données. |
| **E3_model_AI/** | Modèles d’IA et services associés. Inclut l’API FastAPI (texte + image), un prototype Streamlit, les scripts de traitement, les modèles (`xgboost`, `YOLO`), ainsi que les tests. |
| **E4_app_IA/** | Application Django pour les analystes et administrateurs : annotation manuelle, dashboards, journalisation et monitoring via Prometheus. |
| **nginx/** | Configuration Nginx servant le front web et le proxy vers Django. |
| **docker-compose.yml** | Orchestration complète de tous les services (API, Django, monitoring, etc.). |

## Prérequis

- Python 3.10+
- Docker & Docker Compose
- SQLite 3
- (Optionnel) Environnement virtuel pour exécuter localement certains composants

## Mise en place

1. **Cloner le dépôt**

   ```bash
   git clone https://github.com/…/certification_global.git
   cd certification_global

2. **Configurer les fichiers d’environnement**

- E1_gestion_donnees/api/.env (exemple fourni : .env.example)

- E3_model_AI/api_ml/.env (à créer : SECRET_KEY, API_USERNAME, API_PASSWORD, ACCESS_TOKEN_EXPIRE_MINUTES, …)

- .env à la racine pour Django (SECRET_KEY, ENV, DJANGO_LOG_LEVEL, …)

3. **Lancer l’infrastructure en local**
   
  ```bash
  docker compose up --build
  ```


| Service             | URL par défaut                                   |
| ------------------- | ------------------------------------------------ |
| API ML (FastAPI)    | [http://localhost:8000](http://localhost:8000)   |
| API Données         | [http://localhost:7000](http://localhost:7000)   |
| Application Django  | [http://localhost](http://localhost) (via Nginx) |
| Interface Streamlit | [http://localhost:8501](http://localhost:8501)   |
| Prometheus          | [http://localhost:9090](http://localhost:9090)   |
| Grafana             | [http://localhost:3000](http://localhost:3000)   |


## Utilisation rapide

- API Données (E1) : authentification JWT, endpoints /token, /products/, /products/{id}, /products/{id}/images.

- API ML (E3) : endpoints /token, /predict/ (texte + XGBoost), /predict_image/ (images + YOLO), /metrics pour Prometheus, /monitor/* pour les rapports Evidently.

- Application Django (E4) : authentification, annotation manuelle, tableaux de bord analyste/admin, export CSV, logging détaillé.

## Tests

- API & modèles
```bash
pytest E3_model_AI/tests/ --cov=api_ml --cov=model_ml
```

- Django
```bash
cd E4_app_IA
coverage run manage.py test
coverage report
```


## Licence
Aucune licence explicite n’est fournie dans ce dépôt. Veuillez contacter l’auteur ou l’équipe responsable avant toute utilisation en production ou redistribution.

Ce README global offre une vue d’ensemble pour naviguer et démarrer rapidement avec le projet ; référez‑vous aux sous‑répertoires pour une documentation plus détaillée.
  
