class BusinessRouter:
    app_label = "soporte"

    def db_for_read(self, model, **hints):
        return "negocio" if model._meta.app_label == self.app_label else None

    def db_for_write(self, model, **hints):
        return "negocio" if model._meta.app_label == self.app_label else None

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if self.app_label in labels:
            return len(labels) == 1
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return db == "negocio"
        return db == "default"

