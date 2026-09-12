#!/usr/bin/env bash
#
# Bring the whole SecureTrack stack up with one command.
#
#   ./run-local.sh            build images, start backend + frontend, wait for health
#   ./run-local.sh --seed     ...and load sample assets/findings once it is up
#   ./run-local.sh --logs     ...and then follow the logs (Ctrl-C stops following,
#                             the stack keeps running)
#   ./run-local.sh --down     stop and remove the stack
#   ./run-local.sh --down -v  ...and delete the SQLite volume as well
#
set -euo pipefail

cd "$(dirname "$0")"

BACKEND_URL="http://localhost:5000"
FRONTEND_URL="http://localhost:5173"

log()  { printf '\033[36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[33m!! \033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31mxx \033[0m %s\n' "$*" >&2; exit 1; }

# --- argument handling -------------------------------------------------------
# Parsed before touching Docker so that --help works on a machine without it.

SEED=0
FOLLOW=0
DOWN=0
DOWN_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed) SEED=1; shift ;;
    --logs) FOLLOW=1; shift ;;
    --down)
      DOWN=1
      shift
      DOWN_ARGS=("$@")   # anything after --down is passed through, e.g. -v
      break
      ;;
    -h|--help) sed -n '3,10p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) die "Unknown option: $1 (try --help)" ;;
  esac
done

# --- docker plumbing ---------------------------------------------------------

command -v docker >/dev/null 2>&1 \
  || die "docker is not installed or not on PATH. Install Docker Desktop: https://docs.docker.com/get-docker/"

if docker compose version >/dev/null 2>&1; then
  compose() { docker compose "$@"; }
elif command -v docker-compose >/dev/null 2>&1; then
  compose() { docker-compose "$@"; }
else
  die "Neither 'docker compose' nor 'docker-compose' is available."
fi

docker info >/dev/null 2>&1 \
  || die "Cannot talk to the Docker daemon. Is Docker Desktop running?"

if [[ "$DOWN" -eq 1 ]]; then
  log "Stopping the stack..."
  compose down ${DOWN_ARGS[@]+"${DOWN_ARGS[@]}"}
  log "Stopped."
  exit 0
fi

# --- bring it up -------------------------------------------------------------

log "Building images and starting containers..."
compose up --build -d

# Compose already waits for the backend healthcheck before starting the
# frontend, but poll from the host too so this script only returns once the
# stack is genuinely reachable from outside Docker.
wait_for() {
  local name="$1" url="$2" attempts=60
  log "Waiting for $name at $url ..."
  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS -o /dev/null --max-time 2 "$url" 2>/dev/null; then
      log "$name is up."
      return 0
    fi
    sleep 1
  done
  warn "$name did not respond after ${attempts}s. Recent logs:"
  compose logs --tail 40
  die "Startup failed."
}

if command -v curl >/dev/null 2>&1; then
  wait_for "backend"  "$BACKEND_URL/health"
  wait_for "frontend" "$FRONTEND_URL/"
else
  warn "curl not found; skipping health polling."
fi

if [[ "$SEED" -eq 1 ]]; then
  log "Seeding sample data..."
  compose exec -T backend python seed.py
fi

cat <<BANNER

  SecureTrack is running.

    Frontend   $FRONTEND_URL
    API        $BACKEND_URL
    Health     $BACKEND_URL/health

    Logs       docker compose logs -f
    Stop       ./run-local.sh --down

BANNER

if [[ "$FOLLOW" -eq 1 ]]; then
  log "Following logs (Ctrl-C to stop following; the stack keeps running)."
  compose logs -f
fi
