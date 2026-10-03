#!/bin/sh
# Test a fresh sandbox, then narrow its policy and run the real-data agent.
set -eu
cd "$(dirname "$0")/.."
. scripts/openshell-env.sh
finguard_sandbox="${1:-finguard-$(date +%Y%m%d%H%M%S)}"
.venv/bin/python - <<'PY'
import urllib.request
for port in (18081,18082):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=3) as response:
        assert response.status == 200
PY
echo 'FINGUARD_STAGE:export'
.venv/bin/python scripts/prepare-openshell.py
echo 'FINGUARD_STAGE:build'
docker build --tag finguard-openshell:0.1.2 .local/openshell/build
echo 'FINGUARD_STAGE:control'
docker run --rm --network none finguard-openshell:0.1.2 python -c \
  'from pathlib import Path; import json,os; p=Path("/evidence/transaction.json"); p.write_bytes(p.read_bytes()); print(json.dumps({"uid":os.getuid(),"sealed_read":bool(Path("/sealed/decoy.txt").read_bytes()),"symlink_read":bool(Path("/evidence/secret-link").read_bytes()),"evidence_write":True}))' \
  > artifacts/openshell/filesystem-control.json
echo 'FINGUARD_STAGE:sandbox'
openshell sandbox create --name "$finguard_sandbox" --from finguard-openshell:0.1.2 \
  --policy integration/openshell/test-policy.yaml --cpu 2 --memory 512Mi \
  --approval-mode manual --no-auto-providers --detach -- /bin/sleep infinity
openshell settings set "$finguard_sandbox" --key ocsf_json_enabled --value true
# Wait for observed activation, not just the gateway's saved setting.
.venv/bin/python - "$finguard_sandbox" <<'PY'
import subprocess,sys,time
for _ in range(25):
    logs=subprocess.check_output(['openshell','logs',sys.argv[1],'-n','100'],text=True)
    if 'OCSF JSONL logging toggled' in logs:
        break
    time.sleep(1)
else:
    raise SystemExit('Native audit export did not activate; refusing to continue')
PY
finguard_receipt_offset="$(.venv/bin/python -c 'from pathlib import Path; print(len(Path("artifacts/openshell/receiver.jsonl").read_text().splitlines()))')"
echo 'FINGUARD_STAGE:probes'
openshell sandbox exec --name "$finguard_sandbox" --no-login-shell --workdir /opt/finguard \
  -- python -m finguard.containment_probes
.venv/bin/python - "$finguard_receipt_offset" <<'PY'
from pathlib import Path
import sys
root=Path('artifacts/openshell')
lines=(root/'receiver.jsonl').read_text().splitlines()[int(sys.argv[1]):]
(root/'receiver-run.jsonl').write_text('\n'.join(lines)+'\n')
PY
echo 'FINGUARD_STAGE:policy'
openshell policy set "$finguard_sandbox" --policy integration/openshell/policy.yaml --wait --timeout 30
echo 'FINGUARD_STAGE:investigate'
openshell sandbox exec --name "$finguard_sandbox" --no-login-shell --workdir /opt/finguard \
  -- python -m finguard.contained
echo 'FINGUARD_STAGE:collect'
.venv/bin/python scripts/collect-openshell.py "$finguard_sandbox"
echo 'FINGUARD_STAGE:verify'
.venv/bin/python scripts/verify-openshell.py
