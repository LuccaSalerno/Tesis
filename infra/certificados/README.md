# Certificados de RDS (DO-2026-10-22-OPS P4)

Las funciones se conectan a RDS Proxy y a la instancia con TLS `verify-full`. Para eso el
paquete Lambda incluye un solo archivo de CA (`certificados/ca-bd.pem`) que une:

- el paquete global de Amazon RDS, para la instancia;
- las raíces de Amazon Trust Services (Amazon Root CA 1 a 4), porque RDS Proxy presenta un
  certificado de ACM que no encadena con el paquete de RDS (DIF-96).

**Lo descarga el equipo** desde la documentación oficial de Amazon RDS («Using SSL/TLS to
encrypt a connection to a DB instance», paquete `global-bundle.pem`) y lo guarda como:

```
infra/certificados/rds-global-bundle.pem
infra/certificados/amazon-trust-raices.pem   # AmazonRootCA1..4.pem concatenados, en ese orden
```

Las raíces se descargan de https://www.amazontrust.com/repository/ (`AmazonRootCA1.pem` a
`AmazonRootCA4.pem`); comparar la huella SHA-256 de cada una con la publicada allí.

El repositorio excluye todos los `*.pem` (`.gitignore`), así que no se versiona: se vuelve a
descargar y se compara con el SHA-256 registrado abajo. Es un certificado público, sin secretos.

| Fecha | URL oficial | SHA-256 |
|---|---|---|
| 22/10/2026 | https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem (114 certificados) | `90a6f1a7978a1b1b096dca6c57511ca48d3b8cf052f8e704baf358f34ea2f21b` |
| 23/10/2026 | https://www.amazontrust.com/repository/AmazonRootCA1.pem … AmazonRootCA4.pem, concatenados (huella de Amazon Root CA 1: `8E:CD:E6:88:…:98:19:6E`) | `36dba8e4b8041cd14b9d60158893963301bcbb92e1c456847784de2acb5bd550` |
