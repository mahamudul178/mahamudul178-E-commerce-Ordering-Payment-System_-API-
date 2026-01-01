from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = 'Product Management'
    
    def ready(self):
        """Import signals or other startup code here"""
        pass