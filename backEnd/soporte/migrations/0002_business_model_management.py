from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("soporte", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(name="empresamodel", options={
            "managed": settings.BUSINESS_MODELS_MANAGED, "ordering": ["razon_social"],
        }),
        migrations.AlterModelOptions(name="categoriamodel", options={
            "managed": settings.BUSINESS_MODELS_MANAGED, "ordering": ["nombre"],
        }),
        migrations.AlterModelOptions(name="tecnicomodel", options={
            "managed": settings.BUSINESS_MODELS_MANAGED, "ordering": ["nombre"],
        }),
        migrations.AlterModelOptions(name="ticketmodel", options={
            "managed": settings.BUSINESS_MODELS_MANAGED, "ordering": ["-fecha_creacion"],
        }),
        migrations.AlterModelOptions(name="comentariomodel", options={
            "managed": settings.BUSINESS_MODELS_MANAGED, "ordering": ["numero"],
        }),
    ]
