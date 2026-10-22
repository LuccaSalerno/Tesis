"""Puerto del modelo de embeddings (DO-2026-10-22-RAG). El adaptador real es Cohere Embed
Multilingual v3 en Bedrock (`atlas.integraciones.bedrock`); las pruebas de la lógica
propia usan vectores deterministas (P1 de DO-2026-10-22-PROC)."""

from typing import Literal, Protocol

TipoEntrada = Literal["search_document", "search_query"]


class ModeloEmbeddings(Protocol):
    identificador: str

    def embeber(self, textos: list[str], tipo: TipoEntrada) -> list[list[float]]: ...
