from django.core.management.base import BaseCommand

from soporte.infrastructure.models import CategoriaModel, ComentarioModel, EmpresaModel, TecnicoModel, TicketModel


class Command(BaseCommand):
    help = "Carga datos demostrativos en la base de negocio"

    def handle(self, *args, **options):
        empresas = [
            ("76.111.111-1", "Comercial Andina SpA", "PREMIUM"),
            ("77.222.222-2", "Transportes del Pacífico Ltda.", "BASICO"),
            ("78.333.333-3", "Servicios Médicos Sur SpA", "PREMIUM"),
            ("79.444.444-4", "Constructora Horizonte Ltda.", "BASICO"),
            ("80.555.555-5", "Agrícola Valle Verde SpA", "BASICO"),
        ]
        for rut, nombre, plan in empresas:
            EmpresaModel.objects.get_or_create(rut=rut, defaults={"razon_social": nombre, "plan": plan, "activo": True})
        categorias = [("Acceso y contraseñas", 4), ("Correo electrónico", 8), ("Red y conectividad", 4), ("Equipos y periféricos", 24), ("Software empresarial", 12)]
        for nombre, horas in categorias:
            CategoriaModel.objects.get_or_create(nombre=nombre, defaults={"horas_sla": horas, "activo": True})
        tecnicos = [("15.111.111-1", "Camila Rojas", "camila.rojas@soporteya.cl"), ("16.222.222-2", "Diego Morales", "diego.morales@soporteya.cl"), ("17.333.333-3", "Valentina Soto", "valentina.soto@soporteya.cl"), ("18.444.444-4", "Martín Silva", "martin.silva@soporteya.cl"), ("19.555.555-5", "Paula Contreras", "paula.contreras@soporteya.cl")]
        for rut, nombre, email in tecnicos:
            TecnicoModel.objects.get_or_create(rut=rut, defaults={"nombre": nombre, "email": email, "activo": email != "paula.contreras@soporteya.cl"})
        if not TicketModel.objects.exists():
            t = TicketModel.objects.create(empresa=EmpresaModel.objects.first(), categoria=CategoriaModel.objects.get(nombre="Red y conectividad"), tecnico=TecnicoModel.objects.get(email="camila.rojas@soporteya.cl"), titulo="Sin conexión en oficina central", descripcion="Los equipos del segundo piso no acceden a la red corporativa.", prioridad="CRITICA", estado="EN_PROGRESO")
            ComentarioModel.objects.create(ticket=t, numero=1, autor="Camila Rojas", texto="Se detectó una falla en el switch del segundo piso.")
        self.stdout.write(self.style.SUCCESS("Datos de negocio cargados."))

