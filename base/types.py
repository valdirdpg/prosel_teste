class DictObject:
    def __init__(self, data):
        self.__dict__.update(data)


class Servidor(DictObject):
    @property
    def pk(self):
        return self.matricula

    def __str__(self):
        return f"{self.nome} ({self.matricula}) - {self.campus}"
