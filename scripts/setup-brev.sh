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

.venv/bin/python - "$OUTPUT_DIR" <<'PY'
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
metadata = {"completed_at_utc": datetime.now(timezone.utc).isoformat(), "git_revision": revision,
            "working_tree_dirty": bool(dirty), "python": platform.python_version(),
            "os": platform.system(), "kernel": platform.release(), "architecture": platform.machine(),
            "backend": "virtual_simulation", "seed": 42, "runs_per_mode": 1000,
            "tests": "passed", "gpu_used": False, "openshell_used": False}
(Path(sys.argv[1]) / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
PY
tar -czf "$OUTPUT_DIR.tar.gz" -C "$(dirname "$OUTPUT_DIR")" "$(basename "$OUTPUT_DIR")"

printf '\nFinGuard tests and virtual benchmarks completed. Reports: %s/%s\n' "$PROJECT_ROOT" "$OUTPUT_DIR"
printf '%s\n' 'No LLM, OpenShell sandbox, or GPU workload was launched.'
printf 'Share this results bundle: %s/%s.tar.gz\n' "$PROJECT_ROOT" "$OUTPUT_DIR"
printf '%s\n' 'Optional API: .venv/bin/python -m uvicorn finguard.api:app --host 127.0.0.1 --port 8000'
