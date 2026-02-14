#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALEMBIC_INI="$SCRIPT_DIR/alembic.ini"

if [[ ! -f "$ALEMBIC_INI" ]]; then
  echo "alembic.ini not found at $ALEMBIC_INI" >&2
  exit 1
fi

alembic -c "$ALEMBIC_INI" upgrade head
