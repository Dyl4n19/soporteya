import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaModel',
            fields=[
                ('id_categoria', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=80, unique=True)),
                ('horas_sla', models.PositiveIntegerField()),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'CATEGORIAS_TICKET',
                'ordering': ['nombre'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='EmpresaModel',
            fields=[
                ('id_empresa', models.AutoField(primary_key=True, serialize=False)),
                ('rut', models.CharField(max_length=12, unique=True)),
                ('razon_social', models.CharField(max_length=120)),
                ('plan', models.CharField(choices=[('BASICO', 'Básico'), ('PREMIUM', 'Premium')], max_length=10)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'EMPRESAS',
                'ordering': ['razon_social'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TecnicoModel',
            fields=[
                ('id_tecnico', models.AutoField(primary_key=True, serialize=False)),
                ('rut', models.CharField(max_length=12, unique=True)),
                ('nombre', models.CharField(max_length=120)),
                ('email', models.EmailField(max_length=150, unique=True)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'TECNICOS',
                'ordering': ['nombre'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TicketModel',
            fields=[
                ('id_ticket', models.AutoField(primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=150)),
                ('descripcion', models.TextField()),
                ('prioridad', models.CharField(choices=[('BAJA', 'Baja'), ('MEDIA', 'Media'), ('ALTA', 'Alta'), ('CRITICA', 'Critica')], default='MEDIA', max_length=10)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_cierre', models.DateTimeField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('ABIERTO', 'Abierto'), ('ASIGNADO', 'Asignado'), ('EN_PROGRESO', 'En Progreso'), ('RESUELTO', 'Resuelto'), ('CERRADO', 'Cerrado')], default='ABIERTO', max_length=15)),
                ('categoria', models.ForeignKey(db_column='id_categoria', on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='soporte.categoriamodel')),
                ('empresa', models.ForeignKey(db_column='id_empresa', on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='soporte.empresamodel')),
                ('tecnico', models.ForeignKey(blank=True, db_column='id_tecnico', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='soporte.tecnicomodel')),
            ],
            options={
                'db_table': 'TICKETS',
                'ordering': ['-fecha_creacion'],
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ComentarioModel',
            fields=[
                ('id_comentario', models.AutoField(primary_key=True, serialize=False)),
                ('numero', models.PositiveIntegerField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('autor', models.CharField(max_length=120)),
                ('texto', models.TextField()),
                ('ticket', models.ForeignKey(db_column='id_ticket', on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='soporte.ticketmodel')),
            ],
            options={
                'db_table': 'COMENTARIOS_TICKET',
                'ordering': ['numero'],
                'managed': True,
                'constraints': [models.UniqueConstraint(fields=('ticket', 'numero'), name='pk_comentarios_ticket')],
            },
        ),
    ]
