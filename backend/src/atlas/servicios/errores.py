"""Errores del dominio, traducidos a HTTP por la API. Sus mensajes no llevan datos."""


class ErrorDominio(Exception):
    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)
        self.detalle = detalle


class NoEncontrado(ErrorDominio):
    pass


class Conflicto(ErrorDominio):
    pass


class NoPermitido(ErrorDominio):
    """El actor tiene acceso al recurso pero no puede ejecutar la operación (RN-08)."""
