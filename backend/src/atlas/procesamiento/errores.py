"""Errores de las etapas. Su nombre es lo que Step Functions usa para decidir reintentos
(RC-P08.1) y su mensaje es solo un código técnico: nunca contenido documental."""


class ErrorEtapa(Exception):
    def __init__(self, codigo: str) -> None:
        super().__init__(codigo)
        self.codigo = codigo


class ErrorTransitorio(ErrorEtapa):
    """Puede resolverse reintentando la misma operación (limitación de tasa, red, 5xx)."""


class ErrorPermanente(ErrorEtapa):
    """Reintentar no cambia el resultado: el trabajo pasa a fallo técnico."""
