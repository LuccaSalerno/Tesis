# Certificados de RDS (DO-2026-10-22-OPS P4)

Las funciones se conectan a RDS Proxy y a la instancia con TLS `verify-full`. Para eso el
paquete Lambda incluye el paquete global de certificados de Amazon RDS.

**Lo descarga el equipo** desde la documentación oficial de Amazon RDS («Using SSL/TLS to
encrypt a connection to a DB instance», paquete `global-bundle.pem`) y lo guarda como:

```
infra/certificados/rds-global-bundle.pem
```

Antes de versionarlo, registrar la fecha de descarga, la URL oficial y su SHA-256 en este
archivo. Es un certificado público: no contiene secretos.

| Fecha | URL oficial | SHA-256 |
|---|---|---|
| PENDIENTE | PENDIENTE | PENDIENTE |
