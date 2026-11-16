class CrudUseCases:
    def __init__(self, repository):
        self.repository = repository

    def obtener(self, pk):
        return self.repository.get(pk)

    def crear(self, data):
        return self.repository.save(data)

    def actualizar(self, pk, data):
        return self.repository.save(data, self.obtener(pk))

    def eliminar(self, pk):
        return self.repository.delete(self.obtener(pk))

