# Monitoreo Operativo del Monorepo

## Objetivo

Registrar cada 5 minutos un snapshot operativo de los despliegues `production` y `staging` sin modificar la aplicación:

- espacio libre en disco
- RAM y swap del host
- branch y commit desplegados
- uso de CPU/RAM por contenedor de cada stack
- jobs activos de simulación
- escenarios creados recientemente
- jobs de simulación creados recientemente
- cambios recientes sobre `parameter_value_audit`

## Script versionado

- Ruta: `backend/scripts/ops_snapshot.sh`

## Archivos generados

Por defecto se escriben en `~/osemosys-monitoring/logs/`:

- `resource_snapshots-YYYYMMDD.csv`
- `recent_activity-YYYYMMDD.csv`
- `active_jobs-YYYYMMDD.csv`
- `container_stats-YYYYMMDD.csv`

La retención por defecto es de 7 días (`RETENTION_DAYS=7`).

### Estructura actual de los CSV

- `resource_snapshots`: una fila por toma, con referencias git de `production` y `staging`
- `recent_activity`: una fila por proyecto y por toma (`project_name`)
- `active_jobs`: una fila por job visible y por proyecto
- `container_stats`: una fila por contenedor y por proyecto

## Instalación por cron

```bash
mkdir -p ~/osemosys-monitoring/logs
chmod +x ~/osemosys-unified-prod/backend/scripts/ops_snapshot.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/procesa01/osemosys-unified-prod/backend/scripts/ops_snapshot.sh >/dev/null 2>&1") | crontab -
```

## Limitaciones actuales

- La creación de escenarios sí queda visible porque `osemosys.scenario` tiene `created_at`.
- Los jobs nuevos sí quedan visibles porque `osemosys.simulation_job` tiene `queued_at`.
- Las ediciones de valores de parámetros sí quedan visibles por `osemosys.parameter_value_audit`.
- Las ediciones de metadata del escenario no tienen una auditoría dedicada ni `updated_at`, así que no se pueden reconstruir bien sin cambios de aplicación.
- El script consulta por defecto dos despliegues:
  - `~/osemosys-unified-prod` con proyecto `osemosys`
  - `~/osemosys-unified-stg` con proyecto `osemosys-public-stg`
- Si alguno de los dos no existe, el script lo omite sin fallar.
