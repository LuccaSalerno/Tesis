# Análisis de la verificación «rds_force_ssl» (e90-seguridad-1)

**Resultado registrado:** configuración 15 de 16; `rds_force_ssl` no cumple. No se modifica
(AGENTS.md §2.9).

**Cómo verificaba:** `describe_db_parameters(DBParameterGroupName=…, Source="user")`, solo la
primera página, buscando `rds.force_ssl = 1`.

**Comprobación manual del operador** (24/10/2026, después de `configuracion`):

```
$ aws rds describe-db-parameters --db-parameter-group-name atlas-demo-postgres16 \
    --query "Parameters[?ParameterName=='rds.force_ssl'].[ParameterValue,Source,ApplyMethod]"
1       system  pending-reboot
$ aws rds describe-db-instances --db-instance-identifier atlas-demo-postgres \
    --query "DBInstances[0].DBParameterGroups"
atlas-demo-postgres16   in-sync
```

El parámetro vale **1** y el grupo está **aplicado** (`in-sync`). En PostgreSQL 16, 1 es el
valor predeterminado y RDS lo informa con origen `system` aunque Terraform lo fije; por eso el
filtro `Source="user"` no lo encontró. La aplicación, además, se conecta con TLS `verify-full`
(DIF-82).

**Conclusión:** falso negativo del método de verificación. Corregido en `cb6c032` (valor
efectivo, todas las páginas, grupo `in-sync`) y vuelto a medir en `e90-seguridad-2`, que solo
repite la verificación de configuración.
