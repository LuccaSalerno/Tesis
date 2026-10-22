"""IA-D01: fijar 65 registros fuente antes de generar documentos o consultar modelos."""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from .comun import CAMPOS, DECISION, ESTADO, digito_cuit, escribir_json


def preparar(root: Path) -> None:
    destino = root / "corpus/e90/registros_fuente.json"
    if destino.exists():
        raise FileExistsError("registros_ya_preparados_no_se_sobrescriben")
    candidatos = []
    n = 98641001
    while len(candidatos) < 12:
        base = f"30{n:08d}"
        digito = digito_cuit(base)
        if digito is not None:
            candidatos.append(
                {
                    "id": f"CUIT-E90-{len(candidatos) + 1:02d}",
                    "cuit": f"30-{n:08d}-{digito}",
                    "estado": "candidato",
                    "consulta_arca": {
                        "estado": "pendiente",
                        "fecha": None,
                        "resultado": None,
                        "evidencia": None,
                    },
                    "advertencia": "Dígito correcto no acredita inexistencia ni ausencia de asignación.",
                }
            )
        n += 1
    with (root / "docs/evaluacion/plan_diseno_corpus_e90.csv").open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        plan = list(csv.DictReader(stream))
    registros = []
    for index, row in enumerate(plan):
        ident = row["caso_plan"]
        tipo = row["tipo"]
        numero = int(ident.rsplit("-", 1)[1])
        partida = row["grupo_previsto"]
        # Separación de registros: rangos, fechas, importes y numeración independientes.
        desplazamiento = index * 3 + (400 if partida == "ajuste" else 0)
        fecha = date(2026, 1, 7) + timedelta(days=desplazamiento)
        cuit = candidatos[index % 12]
        proveedor = f"Entidad Sintética ATLAS E90 {index % 12 + 1:02d} (ficticia)"
        amount = (
            Decimal("73450.00") + Decimal(index * 3719) + Decimal(numero) / 100
        ).quantize(Decimal(".01"))
        moneda = ("ARS", "USD", "EUR")[index % 3]
        valores = {}
        for campo in CAMPOS[tipo]:
            if campo == "numero":
                valores[campo] = ident
            elif campo.startswith("cuit"):
                valores[campo] = cuit["cuit"]
            elif campo in {"contraparte", "proveedor", "emisor"}:
                valores[campo] = proveedor
            elif campo == "moneda":
                valores[campo] = moneda
            elif campo in {"monto_total", "importe_total", "importe"}:
                valores[campo] = str(amount)
            elif campo == "vigencia_desde":
                valores[campo] = fecha.isoformat()
            elif campo == "vigencia_hasta":
                valores[campo] = (fecha + timedelta(days=364)).isoformat()
            else:
                valores[campo] = fecha.isoformat()
        ausentes = []
        if row["casos_dificiles_planificados"] == "campo_ausente":
            ausentes = [
                "fecha_celebracion"
                if tipo == "contrato"
                else "fecha_emision"
                if tipo == "factura"
                else "fecha"
            ]
            for campo in ausentes:
                valores.pop(campo)
        semilla = int.from_bytes(hashlib.sha256(ident.encode()).digest()[:4], "big")
        modalidad = row["formato_previsto"]
        captura = None
        if modalidad in {"pdf_escaneado", "pdf_fotografiado"}:
            degradado = row["casos_dificiles_planificados"] == "escaneo_baja_calidad"
            captura = {
                "metodo": "degradacion_digital_simulada",
                "captura_fisica": False,
                "semilla": semilla,
                "dpi": 110 if degradado else 140,
                "rotacion_grados": 1.7 if degradado else 0.5,
                "desenfoque_radio": 0.65 if degradado else 0.2,
                "ruido_amplitud": 14 if degradado else 5,
                "perspectiva_pixeles": 30 if modalidad == "pdf_fotografiado" else 0,
                "sombra_lateral": modalidad == "pdf_fotografiado",
                "algoritmo": "e90-simulacion-v1",
            }
        registros.append(
            {
                "doc_id": ident,
                "grupo": partida,
                "tipo": tipo,
                "formato": modalidad,
                "plantilla_id": row["plantilla_prevista"],
                "clasificacion_esperada": tipo,
                "caso_dificil": row["casos_dificiles_planificados"],
                "prompt_injection": row["prompt_injection_previsto"] == "si",
                "cuit_id": cuit["id"],
                "valores": valores,
                "ausentes": ausentes,
                "no_aplicables": [],
                "condiciones": {
                    "plazo_entrega_dias": 12 + index % 17,
                    "canal_atencion": "mesa de servicios sintética",
                    "modalidad_entrega": (
                        "retiro coordinado",
                        "entrega en laboratorio",
                        "entrega digital",
                    )[index % 3],
                },
                "captura": captura,
                "semilla": semilla,
                "estado": ESTADO,
                "revisado_por_autores": False,
                "fuente_contractual": "pendiente_aprobacion"
                if tipo == "contrato"
                else None,
                "referencias_relacionadas": [],
            }
        )
    # Dos tríadas enteramente de medición, preparadas antes de generar, para preguntas multidocumento.
    for num in (1, 3):
        docs = [
            r
            for r in registros
            if r["grupo"] == "medicion"
            and r["tipo"] in {"presupuesto", "orden_compra", "factura"}
            and int(r["doc_id"].rsplit("-", 1)[1]) == num
        ]
        contexto = f"E90-CONTEXTO-{num:02d}"
        for r in docs:
            r["contexto_rag"] = contexto
            r["referencias_relacionadas"] = [x["doc_id"] for x in docs if x is not r]
    for r in registros:
        r.setdefault("contexto_rag", "E90-CONTEXTO-" + r["doc_id"])
        if r["plantilla_id"] == "CTR-ARG_A":
            if r["doc_id"] != "E90-M-CTR-03" or r["grupo"] != "medicion":
                raise ValueError("arg_a_fuera_del_alcance_aprobado")
            r["fuente_contractual"] = "ARG_A"
            r["valores"]["moneda"] = "ARS"
            r["condiciones"]["modalidad_entrega"] = (
                "entrega digital de planos y visitas coordinadas al predio sintético"
            )
            r["condiciones"]["canal_atencion"] = (
                "mesa de coordinación del proyecto sintético"
            )
            r["contexto_contractual"] = {
                "comitente": "Laboratorio Sintético E90 (ficticio)",
                "rol_contraparte": "Arquitecto/a, prestador ficticio sin matrícula real",
                "destino": "adecuación de salas de ensayo del predio sintético E90, sin domicilio real",
                "hitos_dias_corridos": {
                    "croquis_preliminar": 4,
                    "anteproyecto": 9,
                    "documentacion_proyecto": 14,
                },
                "monto_total_corresponde_a": "honorarios completos; no presupuesto de construcción",
                "licencia_adaptacion": "CC-BY-NC-SA-4.0",
            }

    escribir_json(
        root / "oraculos/e90/cuit_candidatos.json",
        {"decision": DECISION, "estado": ESTADO, "candidatos": candidatos},
    )
    escribir_json(
        destino,
        {
            "decision": DECISION,
            "estado": ESTADO,
            "version": "e90-candidato-v1",
            "registros": registros,
        },
    )
    print("REGISTROS_CANDIDATOS documentos=65 medicion=50 ajuste=15 cuit=12")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raiz", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args()
    preparar(args.raiz.resolve())


if __name__ == "__main__":
    main()
