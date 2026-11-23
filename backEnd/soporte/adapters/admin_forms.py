from django import forms
from django.forms.models import BaseInlineFormSet

from soporte.application.exceptions import BusinessError
from soporte.container import comentarios, tickets
from soporte.infrastructure.models import ComentarioModel, TicketModel


class TicketAdminForm(forms.ModelForm):
    class Meta:
        model = TicketModel
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if self.errors or not data.get("empresa") or not data.get("categoria"):
            return data
        values = {
            "empresa_id": data["empresa"].pk, "categoria_id": data["categoria"].pk,
            "tecnico_id": data["tecnico"].pk if data.get("tecnico") else None,
            "titulo": data.get("titulo"), "descripcion": data.get("descripcion"),
            "prioridad": data.get("prioridad"),
        }
        try:
            if self.instance.pk:
                tickets.validar_edicion(tickets.obtener(self.instance.pk), values)
            else:
                tickets.validar_datos(values)
        except BusinessError as error:
            field = error.field if error.field in self.fields else None
            if field:
                self.add_error(field, error.message)
            else:
                self.add_error(None, error.message)
        return data


class ComentarioAdminForm(forms.ModelForm):
    class Meta:
        model = ComentarioModel
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        parent = data.get("ticket") or (self.instance.ticket if self.instance.ticket_id else None)
        try:
            comentarios.validar_texto(data.get("texto", ""))
            if parent and parent.estado == "CERRADO":
                self.add_error(None, "No se pueden modificar comentarios de un ticket cerrado")
        except BusinessError as error:
            self.add_error("texto", error.message)
        return data


class ComentarioInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors) or not self.instance.pk:
            return
        parent = tickets.obtener(self.instance.pk)
        changed = any(form.has_changed() for form in self.forms)
        if parent.estado == "CERRADO" and changed:
            raise forms.ValidationError("No se pueden modificar comentarios de un ticket cerrado")
        remaining = [form for form in self.forms if form.cleaned_data
                     and not form.cleaned_data.get("DELETE") and (form.instance.pk or form.has_changed())]
        if parent.estado == "RESUELTO" and not remaining:
            raise forms.ValidationError("Un ticket resuelto debe conservar al menos un comentario")
        for form in remaining:
            if "texto" in form.cleaned_data:
                try:
                    comentarios.validar_texto(form.cleaned_data["texto"])
                except BusinessError as error:
                    raise forms.ValidationError(error.message) from error
