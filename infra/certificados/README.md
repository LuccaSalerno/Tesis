# Certificados de RDS (DO-2026-10-22-OPS P4)

Las funciones se conectan a RDS Proxy y a la instancia con TLS `verify-full`. Para eso el
paquete Lambda incluye el paquete global de certificados de Amazon RDS.

**Lo descarga el equipo** desde la documentación oficial de Amazon RDS («Using SSL/TLS to
encrypt a connection to a DB instance», paquete `global-bundle.pem`) y lo guarda como:

```
infra/certificados/rds-global-bundle.pem
```

El repositorio excluye todos los `*.pem` (`.gitignore`), así que no se versiona: se vuelve a
descargar y se compara con el SHA-256 registrado abajo. Es un certificado público, sin secretos.

| Fecha | URL oficial | SHA-256 |
|---|---|---|
| 22/10/2026 | https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem (114 certificados) | `90a6f1a7978a1b1b096dca6c57511ca48d3b8cf052f8e704baf358f34ea2f21b` |
