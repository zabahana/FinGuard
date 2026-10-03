#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
. scripts/openshell-env.sh
finguard_sandbox="${1:-finguard-verified}"
openshell sandbox exec --name "$finguard_sandbox" --no-login-shell --workdir /opt/finguard \
  -- python -m finguard.contained
.venv/bin/python scripts/collect-openshell.py "$finguard_sandbox"
.venv/bin/python scripts/verify-openshell.py
