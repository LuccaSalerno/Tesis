"""Procesamiento documental asíncrono (§5.3, hito 1.4): Textract, clasificación y extracción.

Las etapas reciben y devuelven solo identificadores y referencias técnicas; el
contenido viaja por S3 (`resultados/{trabajo}/{intento}/`), nunca por Step Functions.
"""
