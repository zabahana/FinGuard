#!/usr/bin/env bash
# Run inside a Brev Linux instance after cloning this repository.
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ is required"'

if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install -e '.[api]' httpx
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m finguard investigate

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
OUTPUT_DIR="artifacts/brev/$RUN_ID"
for mode in unrestricted runtime adaptive; do
  .venv/bin/python -m finguard evaluate --mode "$mode" --count 1000 --seed 42 --output "$OUTPUT_DIR/$mode"
done

printf '\nFinGuard tests and virtual benchmarks completed. Reports: %s/%s\n' "$PROJECT_ROOT" "$OUTPUT_DIR"
printf '%s\n' 'No LLM, OpenShell sandbox, or GPU workload was launched.'
printf '%s\n' 'Optional API: .venv/bin/python -m uvicorn finguard.api:app --host 127.0.0.1 --port 8000'
