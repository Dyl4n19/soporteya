from django.contrib import admin, messages

from soporte.adapters.admin_forms import ComentarioAdminForm, ComentarioInlineFormSet, TicketAdminForm
from soporte.application.exceptions import BusinessError
from soporte.container import comentarios, tickets
from soporte.infrastructure.models import CategoriaModel, ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


admin.site.site_header = "SoporteYa — Mesa de ayuda TI"
admin.site.site_title = "SoporteYa"
admin.site.index_title = "Administración de soporte"


def sync_model(instance, stored):
    for field in stored._meta.concrete_fields:
        setattr(instance, field.attname, getattr(stored, field.attname))
    instance._state.adding = False
    instance._state.db = stored._state.db


class BusinessAdmin(admin.ModelAdmin):
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


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
    formset = ComentarioInlineFormSet
    readonly_fields = ("numero", "autor", "fecha")

    def has_add_permission(self, request, obj=None):
        return (obj is None or obj.estado != "CERRADO") and super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return (obj is None or obj.estado != "CERRADO") and super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + (("texto",) if obj and obj.estado == "CERRADO" else ())


@admin.register(TicketModel)
class TicketAdmin(BusinessAdmin):
    form = TicketAdminForm
    list_display = ("id_ticket", "titulo", "empresa", "categoria", "tecnico", "prioridad", "estado", "fecha_creacion")
    search_fields = ("titulo", "descripcion", "empresa__razon_social")
    list_filter = ("estado", "prioridad", "categoria")
    inlines = [ComentarioInline]
    readonly_fields = ("estado", "fecha_creacion", "fecha_cierre")
    list_select_related = ("empresa", "categoria", "tecnico")
    actions = ["iniciar_atencion", "resolver", "cerrar", "reabrir"]

    def save_model(self, request, obj, form, change):
        values = {field: getattr(obj, field) for field in tickets.editable_fields}
        author = request.user.get_full_name() or request.user.username
        entity = tickets.actualizar(obj.pk, values, author) if change else tickets.crear(values, author)
        sync_model(obj, TicketModel.objects.get(pk=entity.id_ticket))

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        parent = form.instance.pk
        for instance in formset.deleted_objects:
            comentarios.eliminar(parent, instance.numero)
        for instance in instances:
            if instance.pk:
                comentarios.actualizar(parent, instance.numero, instance.texto)
            else:
                comentarios.crear(parent, request.user.get_full_name() or request.user.username, instance.texto)
        formset.save_m2m()

    def has_delete_permission(self, request, obj=None):
        return (obj is None or obj.estado == "ABIERTO") and super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        tickets.eliminar(obj.pk)

    def transition(self, request, queryset, state):
        for obj in queryset:
            try:
                tickets.cambiar_estado(obj.pk, state)
            except BusinessError as error:
                self.message_user(request, f"Ticket #{obj.pk}: {error.message}", messages.ERROR)
            else:
                self.message_user(request, f"Ticket #{obj.pk}: {state}", messages.SUCCESS)

    @admin.action(description="Pasar a EN PROGRESO")
    def iniciar_atencion(self, request, queryset):
        self.transition(request, queryset, "EN_PROGRESO")

    @admin.action(description="Resolver tickets")
    def resolver(self, request, queryset):
        self.transition(request, queryset, "RESUELTO")

    @admin.action(description="Cerrar tickets resueltos")
    def cerrar(self, request, queryset):
        self.transition(request, queryset, "CERRADO")

    @admin.action(description="Reabrir tickets resueltos")
    def reabrir(self, request, queryset):
        self.transition(request, queryset, "EN_PROGRESO")


@admin.register(ComentarioModel)
class ComentarioAdmin(BusinessAdmin):
    form = ComentarioAdminForm
    list_display = ("ticket", "numero", "autor", "fecha")
    search_fields = ("autor", "texto", "ticket__titulo")
    list_filter = ("fecha", "ticket__estado")
    readonly_fields = ("numero", "autor", "fecha")
    list_select_related = ("ticket",)

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + (("ticket",) if obj else ())

    def save_model(self, request, obj, form, change):
        if change:
            entity = comentarios.actualizar(obj.ticket_id, obj.numero, obj.texto)
        else:
            entity = comentarios.crear(obj.ticket_id, request.user.get_full_name() or request.user.username, obj.texto)
        sync_model(obj, ComentarioModel.objects.get(ticket_id=entity.id_ticket, numero=entity.numero))

    def has_delete_permission(self, request, obj=None):
        if obj and (obj.ticket.estado == "CERRADO" or
                    (obj.ticket.estado == "RESUELTO" and obj.ticket.comentarios.count() == 1)):
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        comentarios.eliminar(obj.ticket_id, obj.numero)

