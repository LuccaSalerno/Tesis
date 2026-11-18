"""El contrato que usa la aplicación web coincide con el de la API."""

from pathlib import Path

from atlas.herramientas import exportar_openapi
from tests.conftest import RAIZ_BACKEND

VERSIONADO = RAIZ_BACKEND.parent / "frontend" / "openapi.json"


def test_f2_el_contrato_versionado_esta_al_dia() -> None:
    assert VERSIONADO.read_text(encoding="utf-8") == exportar_openapi.contenido(), (
        "Regenerar: python -m atlas.herramientas.exportar_openapi ../frontend/openapi.json"
        " y luego npm run tipos en frontend/"
    )


def test_f2_exportar_escribe_el_archivo(tmp_path: Path) -> None:
    destino = tmp_path / "openapi.json"
    assert exportar_openapi.main([str(destino)]) == 0
    assert destino.read_text(encoding="utf-8") == exportar_openapi.contenido()
