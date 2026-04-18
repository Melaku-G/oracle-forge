#!/usr/bin/env bash
# Load DataAgentBench datasets into oracle-forge: local db/ files + optional PostgreSQL + MongoDB.
#
# Source layout: DAB_ROOT (default /home/ubuntu/shared/DataAgentBench) with query_<DATASET>/query_dataset/
#
# Note: agent_core.py reads SQLite/DuckDB from DAB_ROOT (same files, original paths). This script
# additionally mirrors .db files into repo db/ for MCP paths and backups. PostgreSQL + MongoDB
# loads target the running servers (what powers crm_support_query, bookreview_query, etc.).
#
# Usage (from repo root):
#   bash scripts/load_datasets_from_dab.sh                    # all datasets
#   bash scripts/load_datasets_from_dab.sh GITHUB_REPOS DEPS_DEV_V1
#   FILES_ONLY=1 bash scripts/load_datasets_from_dab.sh     # SQLite/DuckDB copies only (no psql/mongorestore)
#   PG_LOAD=0 bash scripts/load_datasets_from_dab.sh         # skip PostgreSQL
#   MONGO_LOAD=0 bash scripts/load_datasets_from_dab.sh      # skip MongoDB
#   PG_DROP_DB=1 bash scripts/load_datasets_from_dab.sh      # DROP + recreate PG DBs before load (destructive)
#
# Schedule (team) — add dataset / test windows:
#   crmarenapro     07:00–07:30 / 07:30–08:00   Mamaru
#   agnews          08:00–08:30 / 08:30–09:00   Nati
#   DEPS_DEV_V1     09:00–09:30 / 09:30–10:00   Rahel
#   GITHUB_REPOS    10:00–10:30 / 10:30–11:00   Yakob
#   googlelocal     11:00–11:30 / 11:30–12:00   Ramlla
#   music_brainz_20k 12:00–12:30 / 12:30–13:00  Melaku
#   PANCANCER_ATLAS 13:00–13:30 / 13:30–14:00   Mamaru
#   PATENTS         14:00–14:30 / 14:30–15:00   Nati (large SQL on Drive may be ~5GB)
#   stockindex      15:00–15:30 / 15:30–16:00   Rahel
#   stockmarket     16:00–16:30 / 16:30–17:00   Yakob
#
# Logs: logs/dataset_load.log (append). Create logs/ automatically.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAB_ROOT="${DAB_ROOT:-/home/ubuntu/shared/DataAgentBench}"
DST="${ROOT}/db"
LOG_DIR="${ROOT}/logs"
LOG_FILE="${LOG_DIR}/dataset_load.log"
FILES_ONLY="${FILES_ONLY:-0}"
PG_LOAD="${PG_LOAD:-1}"
MONGO_LOAD="${MONGO_LOAD:-1}"
PG_DROP_DB="${PG_DROP_DB:-0}"

# shellcheck disable=SC1090
if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "${ROOT}/.env"
  set +a
fi

POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-oracle_forge}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
MONGO_HOST="${MONGO_HOST:-127.0.0.1}"
MONGO_PORT="${MONGO_PORT:-27017}"

# DB names (match DataAgentBench db_config.yaml / MCP defaults)
BOOKREVIEW_POSTGRES_DB="${BOOKREVIEW_POSTGRES_DB:-bookreview_db}"
CRM_SUPPORT_POSTGRES_DB="${CRM_SUPPORT_POSTGRES_DB:-crm_support}"
PANCANCER_POSTGRES_DB="${PANCANCER_POSTGRES_DB:-pancancer_clinical}"
GOOGLELOCAL_POSTGRES_DB="${GOOGLELOCAL_POSTGRES_DB:-googlelocal_db}"
PATENT_CPC_POSTGRES_DB="${PATENT_CPC_POSTGRES_DB:-patent_CPCDefinition}"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

log() {
  local line="[$(ts)] $*"
  echo "$line"
  mkdir -p "$LOG_DIR"
  echo "$line" >>"$LOG_FILE"
}

die() { log "ERROR $*"; exit 1; }

copy_one() {
  local src="$1" dest="$2"
  [[ -f "$src" ]] || { log "SKIP missing source: $src"; return 1; }
  mkdir -p "$(dirname "$dest")"
  local out
  out="$(cp -v --preserve=timestamps "$src" "$dest" 2>&1)" || {
    log "COPY FAILED: $out"
    return 1
  }
  log "COPY $out"
  if [[ -f "$dest" ]]; then
    log "OK size bytes=$(stat -c%s "$dest" 2>/dev/null || stat -f%z "$dest" 2>/dev/null) dst=$dest"
  fi
}

psql_base() {
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$@"
}

pg_ready() {
  [[ "$FILES_ONLY" == "1" ]] && return 1
  [[ "$PG_LOAD" == "0" ]] && return 1
  command -v psql >/dev/null 2>&1 || { log "SKIP psql not installed"; return 1; }
  [[ -n "${POSTGRES_PASSWORD}" ]] || { log "SKIP PostgreSQL: POSTGRES_PASSWORD empty (set in .env)"; return 1; }
  return 0
}

pg_ensure_db() {
  local dbname="$1"
  local exists
  exists="$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='${dbname}'" || true)"
  if [[ "$exists" == "1" ]]; then
    if [[ "$PG_DROP_DB" == "1" ]]; then
      log "PG DROP DATABASE ${dbname}"
      psql_base -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"${dbname}\" WITH (FORCE);"
      psql_base -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${dbname}\";"
    fi
  else
    log "PG CREATE DATABASE ${dbname}"
    psql_base -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${dbname}\";"
  fi
}

pg_load_sql() {
  local label="$1" dbname="$2" sqlfile="$3"
  pg_ready || return 0
  [[ -f "$sqlfile" ]] || { log "SKIP $label missing $sqlfile"; return 1; }
  log "PG START $label -> db=${dbname} file=${sqlfile}"
  pg_ensure_db "$dbname"
  if ! psql_base -d "$dbname" -v ON_ERROR_STOP=1 -f "$sqlfile" >>"${LOG_DIR}/pg_${label}.log" 2>&1; then
    log "PG FAIL $label — see ${LOG_DIR}/pg_${label}.log"
    return 1
  fi
  log "PG OK $label"
}

mongo_ready() {
  [[ "$FILES_ONLY" == "1" ]] && return 1
  [[ "$MONGO_LOAD" == "0" ]] && return 1
  command -v mongorestore >/dev/null 2>&1 || { log "SKIP mongorestore not installed"; return 1; }
  return 0
}

mongo_restore_dir() {
  local label="$1" dump_dir="$2"
  mongo_ready || return 0
  [[ -d "$dump_dir" ]] || { log "SKIP $label missing dir $dump_dir"; return 1; }
  log "MONGO START $label dir=$dump_dir"
  local uri="mongodb://${MONGO_HOST}:${MONGO_PORT}/"
  if mongorestore --uri="$uri" --drop --dir="$dump_dir" >>"${LOG_DIR}/mongo_${label}.log" 2>&1; then
    log "MONGO OK $label"
  else
    log "MONGO FAIL $label — see ${LOG_DIR}/mongo_${label}.log"
    return 1
  fi
}

# --- dataset implementations ---

load_yelp() {
  log "=== DATASET yelp (MongoDB + DuckDB) — already on box: refresh ==="
  copy_one "${DAB_ROOT}/query_yelp/query_dataset/yelp_user.db" "${DST}/yelp_user.db"
  mongo_restore_dir "yelp_yelp_business" "${DAB_ROOT}/query_yelp/query_dataset/yelp_business"
}

load_bookreview() {
  log "=== DATASET bookreview (PostgreSQL + SQLite) — already on box: refresh ==="
  copy_one "${DAB_ROOT}/query_bookreview/query_dataset/review_query.db" "${DST}/bookreview_review_query.db"
  pg_load_sql "bookreview_books" "$BOOKREVIEW_POSTGRES_DB" "${DAB_ROOT}/query_bookreview/query_dataset/books_info.sql"
}

load_crmarenapro() {
  log "=== DATASET crmarenapro (SQLite + DuckDB + PostgreSQL) ==="
  copy_one "${DAB_ROOT}/query_crmarenapro/query_dataset/core_crm.db" "${DST}/crm_core_crm.db"
  copy_one "${DAB_ROOT}/query_crmarenapro/query_dataset/products_orders.db" "${DST}/crm_products_orders.db"
  copy_one "${DAB_ROOT}/query_crmarenapro/query_dataset/territory.db" "${DST}/crm_territory.db"
  copy_one "${DAB_ROOT}/query_crmarenapro/query_dataset/sales_pipeline.duckdb" "${DST}/crm_sales_pipeline.duckdb"
  copy_one "${DAB_ROOT}/query_crmarenapro/query_dataset/activities.duckdb" "${DST}/crm_activities.duckdb"
  pg_load_sql "crm_support" "$CRM_SUPPORT_POSTGRES_DB" "${DAB_ROOT}/query_crmarenapro/query_dataset/support.sql"
}

load_agnews() {
  log "=== DATASET agnews (MongoDB + SQLite) ==="
  copy_one "${DAB_ROOT}/query_agnews/query_dataset/metadata.db" "${DST}/agnews_metadata.db"
  mongo_restore_dir "agnews_articles" "${DAB_ROOT}/query_agnews/query_dataset/agnews_articles"
}

load_deps_dev() {
  log "=== DATASET DEPS_DEV_V1 (SQLite + DuckDB) ==="
  copy_one "${DAB_ROOT}/query_DEPS_DEV_V1/query_dataset/package_query.db" "${DST}/deps_dev_package_query.db"
  copy_one "${DAB_ROOT}/query_DEPS_DEV_V1/query_dataset/project_query.db" "${DST}/deps_dev_project_query.db"
}

load_github_repos() {
  log "=== DATASET GITHUB_REPOS (SQLite + DuckDB) ==="
  copy_one "${DAB_ROOT}/query_GITHUB_REPOS/query_dataset/repo_metadata.db" "${DST}/github_repos_metadata.db"
  copy_one "${DAB_ROOT}/query_GITHUB_REPOS/query_dataset/repo_artifacts.db" "${DST}/github_repos_artifacts.db"
}

load_googlelocal() {
  log "=== DATASET googlelocal (PostgreSQL + SQLite) ==="
  copy_one "${DAB_ROOT}/query_googlelocal/query_dataset/review_query.db" "${DST}/googlelocal_review_query.db"
  pg_load_sql "googlelocal_business" "$GOOGLELOCAL_POSTGRES_DB" "${DAB_ROOT}/query_googlelocal/query_dataset/business_description.sql"
}

load_music_brainz() {
  log "=== DATASET music_brainz_20k (SQLite + DuckDB) ==="
  copy_one "${DAB_ROOT}/query_music_brainz_20k/query_dataset/tracks.db" "${DST}/music_brainz_tracks.db"
  copy_one "${DAB_ROOT}/query_music_brainz_20k/query_dataset/sales.duckdb" "${DST}/music_brainz_sales.duckdb"
}

load_pancancer() {
  log "=== DATASET PANCANCER_ATLAS (PostgreSQL + DuckDB) ==="
  copy_one "${DAB_ROOT}/query_PANCANCER_ATLAS/query_dataset/pancancer_molecular.db" "${DST}/pancancer_molecular.db"
  pg_load_sql "pancancer_clinical" "$PANCANCER_POSTGRES_DB" "${DAB_ROOT}/query_PANCANCER_ATLAS/query_dataset/pancancer_clinical.sql"
}

load_patents() {
  log "=== DATASET PATENTS (PostgreSQL + SQLite) — publication SQLite may be large / absent ==="
  local pub="${DAB_ROOT}/query_PATENTS/query_dataset/patent_publication.db"
  if [[ -f "$pub" ]]; then
    copy_one "$pub" "${DST}/patent_publication.db"
  else
    log "WARN patent_publication.db not found under DAB (optional / may be on Google Drive ~5GB)"
  fi
  pg_load_sql "patent_CPC" "$PATENT_CPC_POSTGRES_DB" "${DAB_ROOT}/query_PATENTS/query_dataset/patent_CPCDefinition.sql"
}

load_stockindex() {
  log "=== DATASET stockindex (SQLite + DuckDB) ==="
  copy_one "${DAB_ROOT}/query_stockindex/query_dataset/indexInfo_query.db" "${DST}/stockindex_indexInfo_query.db"
  copy_one "${DAB_ROOT}/query_stockindex/query_dataset/indextrade_query.db" "${DST}/stockindex_indextrade_query.db"
}

load_stockmarket() {
  log "=== DATASET stockmarket (SQLite + DuckDB) ==="
  copy_one "${DAB_ROOT}/query_stockmarket/query_dataset/stockinfo_query.db" "${DST}/stockmarket_stockinfo_query.db"
  copy_one "${DAB_ROOT}/query_stockmarket/query_dataset/stocktrade_query.db" "${DST}/stockmarket_stocktrade_query.db"
}

# --- main ---

ALL_KEYS=(yelp bookreview crmarenapro agnews DEPS_DEV_V1 GITHUB_REPOS googlelocal music_brainz_20k PANCANCER_ATLAS PATENTS stockindex stockmarket)

log "======== RUN START DAB_ROOT=${DAB_ROOT} DST=${DST} FILES_ONLY=${FILES_ONLY} PG_LOAD=${PG_LOAD} MONGO_LOAD=${MONGO_LOAD} PG_DROP_DB=${PG_DROP_DB}"

if [[ ! -d "$DAB_ROOT" ]]; then
  die "DAB_ROOT not found: $DAB_ROOT"
fi

WANTED=("${ALL_KEYS[@]}")
if [[ $# -gt 0 ]]; then
  WANTED=("$@")
fi

for key in "${WANTED[@]}"; do
  case "$key" in
    yelp) load_yelp ;;
    bookreview) load_bookreview ;;
    crmarenapro) load_crmarenapro ;;
    agnews) load_agnews ;;
    DEPS_DEV_V1) load_deps_dev ;;
    GITHUB_REPOS) load_github_repos ;;
    googlelocal) load_googlelocal ;;
    music_brainz_20k) load_music_brainz ;;
    PANCANCER_ATLAS) load_pancancer ;;
    PATENTS) load_patents ;;
    stockindex) load_stockindex ;;
    stockmarket) load_stockmarket ;;
    *) die "unknown dataset key: $key (use: ${ALL_KEYS[*]})" ;;
  esac
done

log "======== RUN END"
log "Manifest (db/*.db under ${DST}):"
find "$DST" -maxdepth 1 -name '*.db' -type f -printf '%s %p\n' 2>/dev/null | sort -nr | while read -r sz path; do
  log "  $sz bytes  $path"
done || true
