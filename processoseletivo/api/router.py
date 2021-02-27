from processoseletivo.api import viewsets

router = [
    (r"processos-seletivos", viewsets.ProcessoSeletivoViewSet),
    (r"candidatos", viewsets.CandidatoViewSet),
]
