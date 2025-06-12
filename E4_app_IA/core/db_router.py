import os

class WeaponDataRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'core' and model.__name__ != 'AnnotationManuelle':
            return 'weapon_data'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'core' and model.__name__ != 'AnnotationManuelle':
            return 'weapon_data'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'weapon_data':
            return os.environ.get("TESTING") == "true"
        return None