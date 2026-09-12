#!/usr/bin/env bash
#
# Run the SecureTrack test suites.
#
#   ./test-local.sh              both suites inside Docker (no local toolchain needed)
#   ./test-local.sh --local      both suites natively, using backend/.venv and npm
#   ./test-local.sh backend      just the pytest suite
#   ./test-local.sh frontend     just the vitest suite
#
# The target and --local can be combined, e.g. ./test-local.sh --local backend
#
set -euo pipefail

cd "$(dirname "$0")"

log()  { printf '\033[36m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[31mxx \033[0m %s\n' "$*" >&2; exit 1; }

MODE="docker"
TARGET="all"

for arg in "$@"; do
  case "$arg" in
    --local)          MODE="local" ;;
    --docker)         MODE="docker" ;;
    backend|frontend) TARGET="$arg" ;;
    -h|--help)        sed -n '2,10p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) die "Unknown argument: $arg (try --help)" ;;
  esac
done

# Plain assignments rather than `[[ ... ]] && var=1`, which would return
# non-zero when the test fails and trip `set -e`.
run_backend=0
run_frontend=0
if [[ "$TARGET" == "all" || "$TARGET" == "backend" ]]; then
  run_backend=1
fi
if [[ "$TARGET" == "all" || "$TARGET" == "frontend" ]]; then
  run_frontend=1
fi

failed=()

# --- docker mode -------------------------------------------------------------

if [[ "$MODE" == "docker" ]]; then
  command -v docker >/dev/null 2>&1 \
    || die "docker is not installed or not on PATH. Use ./test-local.sh --local instead."
  docker info >/dev/null 2>&1 \
    || die "Cannot talk to the Docker daemon. Is Docker Desktop running?"

  if docker compose version >/dev/null 2>&1; then
    compose() { docker compose "$@"; }
  elif command -v docker-compose >/dev/null 2>&1; then
    compose() { docker-compose "$@"; }
  else
    die "Neither 'docker compose' nor 'docker-compose' is available."
  fi

  if [[ "$run_backend" -eq 1 ]]; then
    log "Backend tests (pytest, in Docker)"
    # Rebuild first: `compose run` reuses an existing image and would otherwise
    # test whatever the last build captured rather than the current source.
    compose build backend || die "Could not build the backend image."
    # --no-deps: the suite uses an in-memory database and needs nothing else running.
    compose run --rm --no-deps -T backend python -m pytest -q \
      || failed+=("backend")
  fi

  if [[ "$run_frontend" -eq 1 ]]; then
    log "Frontend tests (vitest, in Docker)"
    # The runtime image is nginx and has no Node, so build the dedicated test
    # stage from frontend/Dockerfile and run that instead.
    docker build --target test -t securetrack-frontend-test ./frontend \
      || die "Could not build the frontend test image."
    docker run --rm securetrack-frontend-test \
      || failed+=("frontend")
  fi

# --- local mode --------------------------------------------------------------

else
  if [[ "$run_backend" -eq 1 ]]; then
    log "Backend tests (pytest, local)"
    if [[ -x backend/.venv/Scripts/python.exe ]]; then
      PY="./.venv/Scripts/python.exe"          # Windows virtualenv layout
    elif [[ -x backend/.venv/bin/python ]]; then
      PY="./.venv/bin/python"                  # POSIX virtualenv layout
    else
      command -v python >/dev/null 2>&1 || die "No python found and no backend/.venv."
      PY="python"
      log "No backend/.venv found; falling back to the python on PATH."
    fi
    ( cd backend && "$PY" -m pytest -q ) || failed+=("backend")
  fi

  if [[ "$run_frontend" -eq 1 ]]; then
    log "Frontend tests (vitest, local)"
    command -v npm >/dev/null 2>&1 || die "npm is not installed or not on PATH."
    [[ -d frontend/node_modules ]] || ( cd frontend && log "Installing dependencies..." && npm ci )
    ( cd frontend && npm run test ) || failed+=("frontend")
  fi
fi

# --- summary -----------------------------------------------------------------

echo
if [[ ${#failed[@]} -eq 0 ]]; then
  printf '\033[32m==> All requested test suites passed.\033[0m\n'
else
  printf '\033[31m==> Failing suite(s): %s\033[0m\n' "${failed[*]}"
  exit 1
fi
