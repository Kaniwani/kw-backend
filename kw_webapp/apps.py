from django.apps import AppConfig


class KaniwaniConfig(AppConfig):
    name = "kw_webapp"
    verbose_name = "KaniWani"

    def ready(self):
        import kw_webapp.signals
        import api.signals
