"""Errores del dominio, traducidos a HTTP por la API. Sus mensajes no llevan datos."""


class ErrorDominio(Exception):
    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)
        self.detalle = detalle


class NoEncontrado(ErrorDominio):
    pass


class Conflicto(ErrorDominio):
    pass
