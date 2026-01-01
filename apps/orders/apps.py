from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Order Management'
    
    def ready(self):
        """Import signals or other startup code here"""
        pass