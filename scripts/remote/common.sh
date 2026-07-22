#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -n "${HARNESS_ENV_FILE:-}" ]]; then
  if [[ ! -f "$HARNESS_ENV_FILE" ]]; then
    echo "HARNESS_ENV_FILE does not exist: $HARNESS_ENV_FILE" >&2
    exit 2
  fi
  set -a
  # shellcheck disable=SC1090
  source "$HARNESS_ENV_FILE"
  set +a
elif [[ -f "$ROOT_DIR/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.local"
  set +a
elif [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

require_env() {
  local variable_name="$1"
  if [[ -z "${!variable_name:-}" ]]; then
    echo "$variable_name is required. Set it in .env.local; see .env.example." >&2
    exit 2
  fi
}
