from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea roles y usuarios demostrativos (solo desarrollo)"

    def handle(self, *args, **options):
        supervisor, _ = Group.objects.get_or_create(name="SUPERVISOR")
        tecnico, _ = Group.objects.get_or_create(name="TECNICO")
        supervisor.permissions.set(Permission.objects.all())
        tecnico.permissions.set(Permission.objects.filter(codename__in=["view_ticketmodel", "change_ticketmodel", "view_comentariomodel", "add_comentariomodel"]))

        admin, created = User.objects.get_or_create(username="supervisor", defaults={"email": "supervisor@soporteya.cl", "first_name": "Super", "last_name": "Visor", "is_staff": True, "is_superuser": True})
        if created: admin.set_password("Cambiar123!"); admin.save()
        admin.groups.add(supervisor)

        tech, created = User.objects.get_or_create(username="tecnico", defaults={"email": "camila.rojas@soporteya.cl", "first_name": "Camila", "last_name": "Rojas"})
        if created: tech.set_password("Cambiar123!"); tech.save()
        tech.groups.add(tecnico)
        self.stdout.write(self.style.SUCCESS("Roles y usuarios demo creados. Cambie las contraseñas antes de entregar."))

