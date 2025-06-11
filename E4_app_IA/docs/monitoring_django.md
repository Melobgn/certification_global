# Monitoring de l'application Django (E4_app_IA)

## Objectif
Surveiller l'application Django dans une approche MLOps : requêtes HTTP, erreurs, base de données, dérives de modèles, etc.

---

## Métriques surveillées

| Métrique Prometheus                          | Seuil critique      | Description                                           | Alerte ? |
|----------------------------------------------|----------------------|--------------------------------------------------------|----------|
| `django_http_requests_total_by_view_method`  | > 500 req/min        | Activité importante sur une vue spécifique             | Oui      |
| `django_http_request_duration_seconds_mean`  | > 2s                 | Vue trop lente                                        | Oui      |
| `django_db_execute_total_by_type`            | > 1000 SELECT/min    | Charge excessive sur la base                          | Non      |
| `drift_share` (Evidently)                    | > 0.3                | Dérive trop forte sur les données                     | Oui      |

---

## Outils techniques utilisés

| Outil         | Rôle                            | Justification technique                          |
|---------------|----------------------------------|--------------------------------------------------|
| `django-prometheus` | Exposition des métriques HTTP/DB | Léger, natif Django, compatible Prometheus      |
| Prometheus    | Collecteur de métriques          | Standard du MLOps, compatible Grafana           |
| Grafana       | Visualisation et alertes         | Visualisation claire, alertes configurables     |
| Evidently AI  | Dérive des modèles               | Spécifique IA, facile à intégrer avec Prometheus|
| (optionnel) Sentry | Journalisation des erreurs Django | Centralisation et détection rapide des erreurs  |

---

## Installation & configuration

Voir `docker-compose.yml` à la racine du projet.

1. Lancer la stack :
```bash
docker-compose up --build -d
