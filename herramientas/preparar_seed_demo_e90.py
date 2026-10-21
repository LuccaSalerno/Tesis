#!/usr/bin/env python3
"""Build a LOCAL, deterministic manifest for ATLAS E90 demo synthetic seed.

This tool never connects to AWS or a database and does not populate the demo.
The AWS/API seed must be implemented after the backend is built and approved.
"""
import argparse
import hashlib
import json
from pathlib import Path

FILES = (
    ("C-v1", "C-v1_Contrato_Mantenimiento_ATLAS.pdf"),
    ("O-v1", "O-v1_Orden_Compra.pdf"),
    ("O-v2", "O-v2_Orden_Compra.pdf"),
    ("F-v1", "F-v1_Factura.pdf"),
    ("F-v2", "F-v2_Factura.pdf"),
)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Local output JSON path")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    corpus = repo / "corpus"
    docs = []
    for role, name in FILES:
        path = corpus / name
        if not path.is_file():
            parser.error(f"Missing candidate corpus PDF: {path}")
        data = path.read_bytes()
        if not data.startswith(b"%PDF-"):
            parser.error(f"Invalid PDF header: {path}")
        docs.append({"label": role, "relative_path": path.relative_to(repo).as_posix(),
                     "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})
    output = {"schema_version": 1, "profile": "ATLAS-E90A-synthetic-disposable",
              "warning": "LOCAL MANIFEST ONLY. Not an AWS seed and not acceptance evidence.",
              "documents": docs, "aws_invocations": 0, "requires_arca_validation": True}
    out = args.output.expanduser().resolve()
    if out.is_relative_to(repo):
        parser.error("Output must be outside repository to avoid accidental committing")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest written: {out} ({len(docs)} candidate PDFs; no AWS calls)")

if __name__ == "__main__":
    main()
