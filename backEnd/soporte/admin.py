from django.contrib import admin

from soporte.infrastructure.models import CategoriaModel, ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


@admin.register(EmpresaModel)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("rut", "razon_social", "plan", "activo")
    search_fields = ("rut", "razon_social")
    list_filter = ("plan", "activo")


@admin.register(CategoriaModel)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "horas_sla", "activo")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(TecnicoModel)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombre", "email", "activo")
    search_fields = ("rut", "nombre", "email")
    list_filter = ("activo",)


class ComentarioInline(admin.TabularInline):
    model = ComentarioModel
    extra = 0


@admin.register(TicketModel)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id_ticket", "titulo", "empresa", "categoria", "tecnico", "prioridad", "estado", "fecha_creacion")
    search_fields = ("titulo", "descripcion", "empresa__razon_social")
    list_filter = ("estado", "prioridad", "categoria")
    inlines = [ComentarioInline]


@admin.register(ComentarioModel)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("ticket", "numero", "autor", "fecha")
    search_fields = ("autor", "texto", "ticket__titulo")

