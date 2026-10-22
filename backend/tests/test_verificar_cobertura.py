"""Verificador de cobertura mínima por módulo (pedido del equipo, 22/10/2026)."""

import json
from pathlib import Path

import pytest

from herramientas_ci.verificar_cobertura import main, modulos_bajo_minimo


def informe(**porcentajes: float) -> dict[str, object]:
    return {"files": {ruta: {"summary": {"percent_covered": p}} for ruta, p in porcentajes.items()}}


def test_detecta_modulos_bajo_el_minimo_aunque_el_total_alcance() -> None:
    datos = informe(**{"a.py": 100.0, "b.py": 89.99, "c.py": 90.0})
    assert set(modulos_bajo_minimo(datos, 90)) == {"b.py"}


@pytest.mark.parametrize(("porcentaje", "salida"), [(95.0, 0), (72.0, 1)])
def test_codigo_de_salida(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], porcentaje: float, salida: int
) -> None:
    ruta = tmp_path / "coverage.json"
    ruta.write_text(json.dumps(informe(**{"src/atlas/x.py": porcentaje})), encoding="utf-8")
    assert main([str(ruta), "--minimo", "90"]) == salida
    texto = capsys.readouterr().out
    assert ("src/atlas/x.py" in texto) is bool(salida)
