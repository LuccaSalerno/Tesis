"""Ejecutor de seguridad de §6.3.3.

`escenario` arma por la API los trámites, cuentas y documentos sintéticos; `matriz` ejecuta
la Tabla 3.II, el acceso directo por identificador, la consulta cruzada, la inmutabilidad del
historial y el caso adversarial; `aws` hace las verificaciones de solo lectura de SEG-02 y
SEG-04 en la cuenta. La misma matriz corre en la CI contra la aplicación local.
"""
