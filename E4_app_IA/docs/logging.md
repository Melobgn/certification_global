# Journalisation de l'application Django (bloc C20)

## Objectif
Permettre la traçabilité des événements critiques et métiers dans l'application Django via le module `logging`, afin de faciliter le monitoring, le débogage et l’alerting dans une approche MLOps.

---

## Structure de la journalisation

Les logs sont organisés par application Django, avec un fichier de log dédié pour chaque app, situé dans `E4_app_IA/logs/`.

| Application | Fichier log        | Logger utilisé       |
|-------------|--------------------|-----------------------|
| `core`      | `logs/core.log`    | `logging.getLogger('core')`  |
| `users`     | `logs/users.log`   | `logging.getLogger('users')` |
| `Global`    | `logs/global.log`  | `logger `root` (par défaut)` |

---

## Configuration dans `settings.py`

```python
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {...},
        'global_file': {'class': 'logging.FileHandler', 'filename': os.path.join(LOG_DIR, 'global.log'), ...},
        'core_file':   {'class': 'logging.FileHandler', 'filename': os.path.join(LOG_DIR, 'core.log'), ...},
        'users_file':  {'class': 'logging.FileHandler', 'filename': os.path.join(LOG_DIR, 'users.log'), ...},
    },
    'root': {
        'handlers': ['console', 'global_file'],
        'level': 'INFO',
    },
    'loggers': {
        'core': {
            'handlers': ['core_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['users_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
