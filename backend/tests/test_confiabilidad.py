"""Ejecutor de §6.3.2 nivel B (DO-2026-10-23-REC P9) contra una API simulada.

La simulación respeta el límite: con más cargas que cupos, las sobrantes quedan en espera y
entran cuando terminan las anteriores; un DOCX vacío falla siempre. No hay AWS.
"""

import argparse
import threading
from pathlib import Path
from typing import Any

import pytest

from atlas.evaluacion import campana as cmp
from atlas.evaluacion import confiabilidad as conf


class ApiSimulada:
    def __init__(self, limite: int) -> None:
        self.limite = limite
        self.ids = 0
        self.archivos: dict[int, dict[str, Any]] = {}
        self._candado = threading.Lock()

    def _id(self) -> int:
        with self._candado:
            self.ids += 1
            return self.ids

    def transferir(self, url: str, encabezados: Any, datos: bytes) -> None:
        return None

    def post(self, ruta: str, rol: str, cuerpo: Any = None) -> Any:
        partes = ruta.strip("/").split("/")
        if ruta == "/tramites":
            return {"id": self._id()}
        if partes[-1] == "cargas":
            carga = self._id()
            self.archivos[carga] = {
                "tramite": int(partes[1]),
                "vacio": cuerpo["nombre"] == "vacio.docx",
                "intento": 1,
            }
            return {"id": carga, "url": "https://s3/x", "encabezados": {}}
        if partes[-1] == "confirmacion":
            with self._candado:
                archivo = self.archivos[int(partes[3])]
                en_curso = sum(
                    a.get("estado") in ("pendiente", "en_ejecucion") for a in self.archivos.values()
                )
                archivo["estado"] = "en_ejecucion" if en_curso < self.limite else "en_espera"
            return {"id": int(partes[3]), "trabajo": {"estado": archivo["estado"], "intento": 1}}
        if partes[-1] == "reintento":
            archivo = self.archivos[int(partes[3])]
            archivo |= {"estado": "en_ejecucion", "intento": archivo["intento"] + 1}
            return {
                "id": int(partes[3]),
                "trabajo": {"estado": "en_ejecucion", "intento": archivo["intento"]},
            }
        raise AssertionError(ruta)

    def get(self, ruta: str, rol: str) -> Any:
        partes = ruta.strip("/").split("/")
        if len(partes) == 2:
            return {"estado": "borrador"}
        # Cada consulta avanza un paso: terminan los que estaban en ejecución y entra la espera.
        with self._candado:
            for archivo in self.archivos.values():
                if archivo.get("estado") == "en_ejecucion":
                    archivo["estado"] = "fallido" if archivo["vacio"] else "completado"
            libres = self.limite - sum(
                a.get("estado") == "en_ejecucion" for a in self.archivos.values()
            )
            for archivo in self.archivos.values():
                if archivo.get("estado") == "en_espera" and libres > 0:
                    archivo["estado"], libres = "en_ejecucion", libres - 1
        return [
            {"id": i, "trabajo": {"estado": a.get("estado"), "intento": a["intento"]}}
            for i, a in self.archivos.items()
            if a["tramite"] == int(partes[1])
        ]


def test_as_nivel_b_espera_y_fallo_definitivo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cmp, "RAIZ_REPOSITORIO", tmp_path)
    monkeypatch.setattr(cmp, "_commit", lambda _: {"commit": "abc", "cambios_sin_commit": False})
    argumentos = argparse.Namespace(campana="c1", limite=3, escenarios=["espera", "fallo"])
    salida = conf.ejecutar(argumentos, ApiSimulada(3), dormir=lambda _: None)  # type: ignore[arg-type]
    assert salida == "confiabilidad:6/6_cumplen"
    with pytest.raises(cmp.ErrorCampana, match="campana_existente"):
        conf.ejecutar(argumentos, ApiSimulada(3), dormir=lambda _: None)  # type: ignore[arg-type]


def test_as_nivel_b_detecta_sobreasignacion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cmp, "RAIZ_REPOSITORIO", tmp_path)
    monkeypatch.setattr(cmp, "_commit", lambda _: {"commit": "abc", "cambios_sin_commit": False})
    argumentos = argparse.Namespace(campana="c2", limite=2, escenarios=["espera"])
    # La API admite hasta 5 aunque el límite declarado sea 2: el criterio lo detecta.
    salida = conf.ejecutar(argumentos, ApiSimulada(5), dormir=lambda _: None)  # type: ignore[arg-type]
    assert salida == "confiabilidad:1/3_cumplen"


def test_as_nivel_b_espera_maxima_y_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    api = ApiSimulada(1)
    api.archivos[1] = {"tramite": 9, "vacio": False, "intento": 1, "estado": "en_espera"}
    api.limite = 0  # nunca hay cupo
    with pytest.raises(RuntimeError, match="trabajos_sin_terminar"):
        conf.observar(
            api,
            9,
            [1],
            conf.Registro(tmp_path / "r.jsonl"),
            "x",
            dormir=lambda _: None,
            maximo_s=-1,
        )  # type: ignore[arg-type]
    monkeypatch.setattr(cmp, "RAIZ_REPOSITORIO", tmp_path)
    (tmp_path / "evaluacion" / "campanas" / "c3").mkdir(parents=True)
    assert conf.main(["--campana", "c3", "--url-api", "https://x", "--cliente-cognito", "c"]) == 1
    monkeypatch.setattr(conf, "tokens_cognito", lambda *_: {"responsable": "t"})
    monkeypatch.setattr(
        conf,
        "escenario_espera",
        lambda *a, **k: {
            "documentos": 1,
            "en_espera_al_confirmar": 1,
            "max_en_curso_observado": 1,
            "limite": 1,
            "completados": 1,
            "fallidos": 0,
        },
    )
    monkeypatch.setattr(cmp, "_commit", lambda _: {"commit": "abc", "cambios_sin_commit": False})
    assert (
        conf.main(
            [
                "--campana",
                "c4",
                "--url-api",
                "https://x",
                "--cliente-cognito",
                "c",
                "--escenarios",
                "espera",
            ]
        )
        == 0
    )
