"""Localizador indicado por una persona: al corregir un dato (§5.3.3) o al justificar un
vínculo por referencia (RF-14)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FuenteIndicada:
    pagina: int | None
    seccion: str | None
    fragmento: str | None

    @property
    def vacia(self) -> bool:
        return self.pagina is None and not self.seccion and not self.fragmento
