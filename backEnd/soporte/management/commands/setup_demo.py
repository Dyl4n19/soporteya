from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea roles y usuarios demostrativos (solo desarrollo)"

    def handle(self, *args, **options):
        supervisor, _ = Group.objects.get_or_create(name="SUPERVISOR")
        tecnico, _ = Group.objects.get_or_create(name="TECNICO")
        business_permissions = Permission.objects.filter(content_type__app_label="soporte")
        supervisor.permissions.set(business_permissions)
        tecnico.permissions.set(business_permissions.filter(codename__in=[
            "view_ticketmodel", "change_ticketmodel", "view_comentariomodel", "add_comentariomodel",
            "view_empresamodel", "view_categoriamodel", "view_tecnicomodel",
        ]))
        self.ensure_user("admin", "CambiarAdmin123!", {"email": "admin@soporteya.cl", "first_name": "Administrador",
                                                       "is_staff": True, "is_superuser": True})
        lead = self.ensure_user("supervisor", "Cambiar123!", {
            "email": "supervisor@soporteya.cl", "first_name": "Super", "last_name": "Visor",
            "is_staff": True, "is_superuser": False,
        })
        lead.groups.add(supervisor)
        tech = self.ensure_user("tecnico", "Cambiar123!", {
            "email": "camila.rojas@soporteya.cl", "first_name": "Camila", "last_name": "Rojas",
            "is_staff": False, "is_superuser": False,
        })
        tech.groups.add(tecnico)
        self.stdout.write(self.style.SUCCESS("Superusuario, dos roles y usuarios de demostración preparados."))
        self.stdout.write("Las contraseñas solo se asignan al crear cada usuario; las existentes se conservan.")

    def ensure_user(self, username, password, defaults):
        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        if created:
            user.set_password(password)
        for field in ("is_staff", "is_superuser"):
            setattr(user, field, defaults[field])
        user.save()
        return user

