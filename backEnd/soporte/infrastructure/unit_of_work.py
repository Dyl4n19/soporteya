from django.db import transaction


class DjangoUnitOfWork:
    def atomic(self):
        return transaction.atomic(using="negocio")
