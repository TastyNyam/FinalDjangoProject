from django.apps import AppConfig

class BriefblogConfig(AppConfig): # Проверь название своего класса
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'briefblog'

    def ready(self):
        from . import signals
