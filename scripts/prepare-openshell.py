"""Build a minimal sandbox context; never copy labels, weights, credentials or host state."""
import json
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finguard.ulb import load_bank, POLICY

root = Path(__file__).resolve().parents[1]
bank = load_bank(root / 'artifacts/ulb')
build = root / '.local/openshell/build'
(build / 'finguard').mkdir(parents=True, exist_ok=True)
(build / 'evidence').mkdir(exist_ok=True)
for name in ['__init__', 'llm', 'ulb', 'runner', 'models', 'policy', 'bank', 'contained', 'containment_probes', 'attack_lab']:
    shutil.copyfile(root / 'finguard' / f'{name}.py', build / 'finguard' / f'{name}.py')
(build / 'evidence/transaction.json').write_text(json.dumps({'row': bank.row, 'score': bank.score, 'threshold': bank.threshold}, indent=2)+'\n')
(build / 'evidence/policy.txt').write_text(POLICY)
shutil.copyfile(root / 'integration/openshell/Dockerfile', build / 'Dockerfile')
print(f'Prepared {bank.transaction_id} without labels in {build}')
