#!/usr/bin/env bash
set -euo pipefail

# Snapshot operativo periódico para los despliegues del monorepo.
# Registra disco/RAM del host, branch/commit desplegados, stats de contenedores
# y actividad reciente de escenarios/jobs sin tocar el código de la aplicación.

BASE_DIR="${BASE_DIR:-$HOME/osemosys-monitoring}"
LOG_DIR="${LOG_DIR:-$BASE_DIR/logs}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
PROD_REPO_ROOT="${PROD_REPO_ROOT:-$HOME/osemosys-unified-prod}"
PROD_PROJECT_NAME="${PROD_PROJECT_NAME:-osemosys}"
STAGING_REPO_ROOT="${STAGING_REPO_ROOT:-$HOME/osemosys-unified-stg}"
STAGING_PROJECT_NAME="${STAGING_PROJECT_NAME:-osemosys-public-stg}"

mkdir -p "$LOG_DIR"

stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
day="$(date -u +%Y%m%d)"
host="$(hostname -s 2>/dev/null || hostname)"

resource_csv="$LOG_DIR/resource_snapshots-$day.csv"
activity_csv="$LOG_DIR/recent_activity-$day.csv"
active_jobs_csv="$LOG_DIR/active_jobs-$day.csv"
container_csv="$LOG_DIR/container_stats-$day.csv"

resource_header="timestamp,host,disk_free_gb,disk_total_gb,disk_used_pct,mem_used_bytes,mem_available_bytes,swap_used_bytes,production_branch,production_commit,staging_branch,staging_commit"
activity_header="timestamp,project_name,running_jobs,queued_jobs,total_jobs_visible,scenarios_created_5m,simulation_jobs_created_5m,parameter_edits_5m"
active_jobs_header="timestamp,project_name,job_id,status,username,scenario_id,scenario_name,solver_name,queued_at,started_at"
container_header="timestamp,project_name,container_name,cpu_perc,mem_usage,mem_perc"

ensure_csv_header() {
  local file="$1"
  local expected_header="$2"
  local legacy_suffix

  if [[ -f "$file" ]]; then
    if [[ "$(head -n 1 "$file")" == "$expected_header" ]]; then
      return 0
    fi
    legacy_suffix="$(date -u +%Y%m%dT%H%M%SZ)"
    mv "$file" "${file%.csv}.legacy-${legacy_suffix}.csv"
  fi

  printf '%s\n' "$expected_header" > "$file"
}

ensure_csv_header "$resource_csv" "$resource_header"
ensure_csv_header "$activity_csv" "$activity_header"
ensure_csv_header "$active_jobs_csv" "$active_jobs_header"
ensure_csv_header "$container_csv" "$container_header"

read -r disk_total_gb _disk_used_gb disk_free_gb disk_used_pct _mount_point < <(
  df -BG --output=size,used,avail,pcent,target / | tail -n 1 | awk '{gsub(/G/,"",$1); gsub(/G/,"",$2); gsub(/G/,"",$3); gsub(/%/,"",$4); print $1, $2, $3, $4, $5}'
)
read -r mem_used mem_available < <(free -b | awk '/^Mem:/ {print $3, $7}')
swap_used="$(free -b | awk '/^Swap:/ {print $3}')"

git_ref_or_na() {
  local repo_root="$1"
  local mode="$2"
  if git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if [[ "$mode" == "branch" ]]; then
      git -C "$repo_root" rev-parse --abbrev-ref HEAD 2>/dev/null || echo na
    else
      git -C "$repo_root" rev-parse --short HEAD 2>/dev/null || echo na
    fi
  else
    echo "na"
  fi
}

prod_branch="$(git_ref_or_na "$PROD_REPO_ROOT" branch)"
prod_commit="$(git_ref_or_na "$PROD_REPO_ROOT" commit)"
staging_branch="$(git_ref_or_na "$STAGING_REPO_ROOT" branch)"
staging_commit="$(git_ref_or_na "$STAGING_REPO_ROOT" commit)"

echo "$stamp,$host,$disk_free_gb,$disk_total_gb,$disk_used_pct,$mem_used,$mem_available,$swap_used,$prod_branch,$prod_commit,$staging_branch,$staging_commit" >> "$resource_csv"

sql_counts="copy (
select
  coalesce(sum(case when status = 'RUNNING' then 1 else 0 end), 0) as running_jobs,
  coalesce(sum(case when status = 'QUEUED' then 1 else 0 end), 0) as queued_jobs,
  count(*) as total_jobs_visible,
  (select count(*) from osemosys.scenario where created_at >= now() - interval '5 minutes') as scenarios_created_5m,
  (select count(*) from osemosys.simulation_job where queued_at >= now() - interval '5 minutes') as simulation_jobs_created_5m,
  (select count(*) from osemosys.parameter_value_audit where created_at >= now() - interval '5 minutes') as parameter_edits_5m
from osemosys.simulation_job
) to stdout with csv"

sql_active_jobs="copy (
select
  j.id,
  j.status,
  coalesce(u.username, ''),
  j.scenario_id,
  replace(coalesce(s.name, ''), ',', ' ') as scenario_name,
  j.solver_name,
  to_char(j.queued_at at time zone 'utc', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'),
  coalesce(to_char(j.started_at at time zone 'utc', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'), '')
from osemosys.simulation_job j
left join core.\"user\" u on u.id = j.user_id
left join osemosys.scenario s on s.id = j.scenario_id
where j.status in ('QUEUED','RUNNING')
order by j.status desc, j.queued_at asc
) to stdout with csv"

append_project_stats() {
  local project_name="$1"
  local repo_root="$2"
  local tmp_file="${container_csv}.${project_name}.tmp"
  local counts_line=""

  if [[ ! -f "${repo_root}/docker-compose.yml" ]]; then
    return 0
  fi

  docker ps --format '{{.Names}}' | grep "^${project_name}-" | while read -r cname; do
    docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}' "$cname" >> "$tmp_file" 2>/dev/null || true
  done

  if [[ -f "$tmp_file" ]]; then
    while IFS= read -r line; do
      [[ -n "$line" ]] && echo "$stamp,$project_name,$line" >> "$container_csv"
    done < "$tmp_file"
    rm -f "$tmp_file"
  fi

  counts_line="$(
    cd "$repo_root" &&
    docker compose -p "$project_name" exec -T db \
      psql -U "${POSTGRES_USER:-osemosys}" -d "${POSTGRES_DB:-osemosys}" -Atqc "$sql_counts" 2>/dev/null || true
  )"
  if [[ -n "$counts_line" ]]; then
    echo "$stamp,$project_name,$counts_line" >> "$activity_csv"
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] && echo "$stamp,$project_name,$line" >> "$active_jobs_csv"
  done < <(
    cd "$repo_root" &&
    docker compose -p "$project_name" exec -T db \
      psql -U "${POSTGRES_USER:-osemosys}" -d "${POSTGRES_DB:-osemosys}" -Atqc "$sql_active_jobs" 2>/dev/null || true
  )
}

append_project_stats "$PROD_PROJECT_NAME" "$PROD_REPO_ROOT"
append_project_stats "$STAGING_PROJECT_NAME" "$STAGING_REPO_ROOT"

find "$LOG_DIR" -type f -name '*.csv' -mtime +"$RETENTION_DAYS" -delete
