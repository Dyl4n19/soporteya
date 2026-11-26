from collections.abc import Mapping

from rest_framework import serializers


class InputSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({field: ["Campo no permitido"] for field in sorted(unknown)})
        return super().to_internal_value(data)


class LoginInputSerializer(InputSerializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


class RutInputSerializer(InputSerializer):
    rut = serializers.RegexField(
        r"\A(?:[1-9][0-9]{0,7}|[1-9][0-9]{0,2}\.[0-9]{3}|[1-9][0-9]?\.[0-9]{3}\.[0-9]{3})-[0-9Kk]\Z",
        max_length=12, error_messages={"invalid": "Ingrese el RUT con guion y dígito verificador, por ejemplo 12.345.678-5"},
    )

    def validate_rut(self, value):
        number, digit = value.replace(".", "").split("-")
        return f"{int(number):,}-{digit.upper()}".replace(",", ".")


class EmpresaInputSerializer(RutInputSerializer):
    razon_social = serializers.CharField(max_length=120)
    plan = serializers.ChoiceField(choices=["BASICO", "PREMIUM"])
    activo = serializers.BooleanField(default=True)


class EmpresaOutputSerializer(serializers.Serializer):
    id_empresa = serializers.IntegerField()
    rut = serializers.CharField()
    razon_social = serializers.CharField()
    plan = serializers.CharField()
    activo = serializers.BooleanField()


class CategoriaInputSerializer(InputSerializer):
    nombre = serializers.CharField(max_length=80)
    horas_sla = serializers.IntegerField(min_value=1, max_value=8760)
    activo = serializers.BooleanField(default=True)


class CategoriaOutputSerializer(serializers.Serializer):
    id_categoria = serializers.IntegerField()
    nombre = serializers.CharField()
    horas_sla = serializers.IntegerField()
    activo = serializers.BooleanField()


class TecnicoInputSerializer(RutInputSerializer):
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
    id_ticket = serializers.SerializerMethodField()
    numero = serializers.IntegerField()
    fecha = serializers.DateTimeField()
    autor = serializers.CharField()
    texto = serializers.CharField()

    def get_id_ticket(self, obj):
        if isinstance(obj, dict):
            return obj["id_ticket"]
        return getattr(obj, "ticket_id", getattr(obj, "id_ticket", None))


class ComentarioInputSerializer(InputSerializer):
    texto = serializers.CharField(min_length=2, max_length=4000)

    def validate(self, attrs):
        if "texto" not in attrs:
            raise serializers.ValidationError({"texto": self.fields["texto"].error_messages["required"]}, code="required")
        return attrs


class ComentarioQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, default="")
    autor = serializers.CharField(required=False, allow_blank=True)
    numero = serializers.IntegerField(min_value=1, required=False)
    ordering = serializers.CharField(required=False, allow_blank=True)


class TicketInputSerializer(InputSerializer):
    empresa_id = serializers.IntegerField(min_value=1)
    categoria_id = serializers.IntegerField(min_value=1)
    tecnico_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    titulo = serializers.CharField(min_length=5, max_length=150)
    descripcion = serializers.CharField(min_length=10)
    prioridad = serializers.ChoiceField(choices=["BAJA", "MEDIA", "ALTA", "CRITICA"], default="MEDIA")
    comentarios = ComentarioInputSerializer(many=True, required=False, max_length=100)


class TicketUpdateSerializer(TicketInputSerializer):
    vencido = serializers.BooleanField(required=False)
    estado = serializers.ChoiceField(choices=["ABIERTO", "ASIGNADO", "EN_PROGRESO", "RESUELTO", "CERRADO"],
                                    required=False)


class TicketQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, default="")
    ordering = serializers.CharField(required=False, allow_blank=True)
    estado = serializers.ChoiceField(choices=["ABIERTO", "ASIGNADO", "EN_PROGRESO", "RESUELTO", "CERRADO"],
                                    allow_blank=True, required=False)
    prioridad = serializers.ChoiceField(choices=["BAJA", "MEDIA", "ALTA", "CRITICA"], allow_blank=True, required=False)
    categoria_id = serializers.IntegerField(min_value=1, required=False)
    tecnico_id = serializers.IntegerField(min_value=1, required=False)


class TicketOutputSerializer(serializers.Serializer):
    id_ticket = serializers.IntegerField()
    empresa_id = serializers.IntegerField()
    empresa_nombre = serializers.CharField()
    categoria_id = serializers.IntegerField()
    categoria_nombre = serializers.CharField()
    horas_sla = serializers.IntegerField()
    vencido = serializers.BooleanField()
    tecnico_id = serializers.IntegerField(allow_null=True)
    tecnico_nombre = serializers.CharField(allow_null=True)
    titulo = serializers.CharField()
    descripcion = serializers.CharField()
    prioridad = serializers.CharField()
    fecha_creacion = serializers.DateTimeField()
    fecha_cierre = serializers.DateTimeField(allow_null=True)
    estado = serializers.CharField()
    comentarios = ComentarioOutputSerializer(many=True)

class EstadoInputSerializer(InputSerializer):
    estado = serializers.ChoiceField(choices=["ASIGNADO", "EN_PROGRESO", "RESUELTO", "CERRADO"])


class TicketVencidoSerializer(serializers.Serializer):
    id_ticket = serializers.IntegerField()
    titulo = serializers.CharField()
    empresa = serializers.CharField()
    estado = serializers.CharField()
    horas_sla = serializers.IntegerField()
    fecha_creacion = serializers.DateTimeField()


class PromedioResolucionSerializer(serializers.Serializer):
    id_tecnico = serializers.IntegerField()
    tecnico = serializers.CharField()
    horas_promedio = serializers.FloatField()


class ReporteSerializer(serializers.Serializer):
    tickets_vencidos = TicketVencidoSerializer(many=True)
    promedio_resolucion_por_tecnico = PromedioResolucionSerializer(many=True)

