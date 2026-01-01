from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'  # এটা MUST be 'apps.users'
    verbose_name = 'User Management'
    
    def ready(self):
        """Import signals or other startup code here"""
        pass