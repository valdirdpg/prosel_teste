from cursos.api import viewsets

router = [
    (r"docentes", viewsets.DocenteViewSet),
    (r"campi", viewsets.CampiViewSet),
    (r"disciplinas", viewsets.DisciplinaCursoViewSet),
    (r"cursos", viewsets.CursoNoCampusViewSet),
]
