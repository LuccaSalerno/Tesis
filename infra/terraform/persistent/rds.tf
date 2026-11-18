# PostgreSQL Multi-AZ (instancia primaria + reserva), E90A.
# Credencial maestra administrada por RDS en Secrets Manager: solo inicialización.

resource "aws_db_subnet_group" "datos" {
  name       = "${local.prefijo}-datos"
  subnet_ids = aws_subnet.datos[*].id
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${local.prefijo}-postgres16"
  family = "postgres16"
  parameter {
    name  = "rds.force_ssl"
    value = "1"
    # RDS lo informa como estático: con "immediate" cada plan lo vuelve a fijar.
    apply_method = "pending-reboot"
  }
}

resource "aws_db_instance" "principal" {
  identifier                          = "${local.prefijo}-postgres"
  engine                              = "postgres"
  engine_version                      = var.rds_version_motor
  instance_class                      = var.rds_clase
  multi_az                            = true
  allocated_storage                   = var.rds_almacenamiento_gib
  storage_type                        = "gp3"
  storage_encrypted                   = true # clave administrada por AWS: sin claves propias residuales
  username                            = "atlas_maestro"
  manage_master_user_password         = true
  iam_database_authentication_enabled = true
  db_subnet_group_name                = aws_db_subnet_group.datos.name
  parameter_group_name                = aws_db_parameter_group.postgres.name
  vpc_security_group_ids              = [aws_security_group.rds.id]
  publicly_accessible                 = false
  backup_retention_period             = 7 # durante la sesión
  copy_tags_to_snapshot               = true
  auto_minor_version_upgrade          = true
  performance_insights_enabled        = false
  apply_immediately                   = true

  # E90A: el retiro aprobado borra la instancia sin snapshot final ni backups retenidos.
  # Mientras retiro_autorizado sea false, la protección impide cualquier borrado.
  deletion_protection      = !var.retiro_autorizado
  skip_final_snapshot      = true
  delete_automated_backups = true
}
