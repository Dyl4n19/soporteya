from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created, dispatch_uid="soporteya_oracle_numeric_timezone")
def configure_oracle_session(sender, connection, **kwargs):
    if connection.vendor == "oracle" and connection.alias == "negocio":
        with connection.cursor() as cursor:
            cursor.execute("ALTER SESSION SET TIME_ZONE = '+00:00'")
