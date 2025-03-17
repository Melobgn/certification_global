## Description
Système de collecte et d'analyse de données produits provenant de sites e-commerce.
Le projet permet de :
- Collecter des données via des spiders Scrapy
- Stocker les données dans une base SQLite
- Gérer le cycle de vie des données selon les normes RGPD

## Technologies utilisées
- Python
- Scrapy
- SQLite
- FastAPI
- Docker

## Installation

Prerequis :
- Python 3.10+
- Docker
- SQLite3

### Configuration 

1.Copier le fichier `.env.example` en `.env` et configurer les variables d'environnement :

```bash
cp api/.env.example api/.env
```

2. Modifier les variables dans api/.env

### Démarrage

```bash
docker compose up --build
```

## Documentation

- [API](docs/api.md)
- [Database](docs/database.md)
- [RGPD](docs/RGPD.md)

