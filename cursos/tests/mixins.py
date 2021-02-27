from ..permissions import DiretoresdeEnsino


class DiretorEnsinoPermissionData:

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        DiretoresdeEnsino().sync()
