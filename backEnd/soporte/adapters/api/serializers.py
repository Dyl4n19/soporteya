from rest_framework import serializers


class EmpresaInputSerializer(serializers.Serializer):
    rut = serializers.CharField(max_length=12)
    razon_social = serializers.CharField(max_length=120)
    plan = serializers.ChoiceField(choices=["BASICO", "PREMIUM"])
    activo = serializers.BooleanField(default=True)


class EmpresaOutputSerializer(serializers.Serializer):
    id_empresa = serializers.IntegerField()
    rut = serializers.CharField()
    razon_social = serializers.CharField()
    plan = serializers.CharField()
    activo = serializers.BooleanField()


class CategoriaInputSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=80)
    horas_sla = serializers.IntegerField(min_value=1, max_value=8760)
    activo = serializers.BooleanField(default=True)


class CategoriaOutputSerializer(serializers.Serializer):
    id_categoria = serializers.IntegerField()
    nombre = serializers.CharField()
    horas_sla = serializers.IntegerField()
    activo = serializers.BooleanField()


class TecnicoInputSerializer(serializers.Serializer):
    rut = serializers.CharField(max_length=12)
    nombre = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=150)
    activo = serializers.BooleanField(default=True)


class TecnicoOutputSerializer(serializers.Serializer):
    id_tecnico = serializers.IntegerField()
    rut = serializers.CharField()
    nombre = serializers.CharField()
    email = serializers.EmailField()
    activo = serializers.BooleanField()


class MasterQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, default="")
    ordering = serializers.CharField(required=False, allow_blank=True)
    activo = serializers.BooleanField(required=False)
    plan = serializers.ChoiceField(choices=["BASICO", "PREMIUM"], required=False, allow_blank=True)


class ComentarioOutputSerializer(serializers.Serializer):
    numero = serializers.IntegerField()
    fecha = serializers.DateTimeField()
    autor = serializers.CharField()
    texto = serializers.CharField()


class TicketInputSerializer(serializers.Serializer):
    empresa_id = serializers.IntegerField(min_value=1)
    categoria_id = serializers.IntegerField(min_value=1)
    tecnico_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    titulo = serializers.CharField(min_length=5, max_length=150)
    descripcion = serializers.CharField(min_length=10)
    prioridad = serializers.ChoiceField(choices=["BAJA", "MEDIA", "ALTA", "CRITICA"], default="MEDIA")


class TicketOutputSerializer(serializers.Serializer):
    id_ticket = serializers.IntegerField()
    empresa_id = serializers.IntegerField()
    empresa_nombre = serializers.CharField(source="empresa.razon_social")
    categoria_id = serializers.IntegerField()
    categoria_nombre = serializers.CharField(source="categoria.nombre")
    horas_sla = serializers.IntegerField(source="categoria.horas_sla")
    tecnico_id = serializers.IntegerField(allow_null=True)
    tecnico_nombre = serializers.SerializerMethodField()
    titulo = serializers.CharField()
    descripcion = serializers.CharField()
    prioridad = serializers.CharField()
    fecha_creacion = serializers.DateTimeField()
    fecha_cierre = serializers.DateTimeField(allow_null=True)
    estado = serializers.CharField()
    comentarios = ComentarioOutputSerializer(many=True)

    def get_tecnico_nombre(self, obj):
        return obj.tecnico.nombre if obj.tecnico else None


class ComentarioInputSerializer(serializers.Serializer):
    texto = serializers.CharField(min_length=2, max_length=4000)


class EstadoInputSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=["ASIGNADO", "EN_PROGRESO", "RESUELTO", "CERRADO"])

