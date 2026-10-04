"""Publish allowlisted model-evaluation counts and synthetic decision traces."""
import json
from pathlib import Path
import hashlib
import sys
from collections import Counter

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from finguard.evaluation_reporting import recovery_metric, recovery_observation

summary=json.loads((root/'artifacts/model-eval/latest.json').read_text())
if not summary['complete'] or summary['phase']!='main':
    raise SystemExit('Only a fully finished main evaluation can be published')
run=root/'artifacts/model-eval'/summary['run_id']
raw_trials={}
for entry in summary['trial_index']:
    path=run/f"{entry['id']}.json"
    if hashlib.sha256(path.read_bytes()).hexdigest()!=summary['trial_files_sha256'][entry['id']]:
        raise SystemExit(f"Trial integrity mismatch: {entry['id']}")
    raw_trials[entry['id']]=json.loads(path.read_text())
    entry['recovery']=recovery_observation(raw_trials[entry['id']])
for cohort in ('benign','multi'):
    rows=[t for t in raw_trials.values() if t['cohort']==cohort]
    summary['cohorts'][cohort]['metrics']['rr']=recovery_metric(rows)
    summary['cohorts'][cohort]['prohibited_reasons']=dict(Counter(p['oracle_reason'] for t in rows for p in t['proposals'] if p['prohibited']))
summary['reporting_derivations']={
    'recovery':'Post-hoc analysis of the original saved traces; no new model runs or changes to the frozen evaluation.',
    'source_sha256':hashlib.sha256((root/'finguard/evaluation_reporting.py').read_bytes()).hexdigest()}
summary['trace_examples']=[]
for cohort in ('single','multi','benign'):
    rows=[t for t in summary['trial_index'] if t['cohort']==cohort]
    rows.sort(key=lambda t:(not t['recovery']['recovered'],-t['prohibited_proposals'],t['id']))
    for entry in rows[:3]:
        raw=raw_trials[entry['id']]
        summary['trace_examples'].append({**entry,'proposals':[
            {'turn':p['turn'],'tool':p['call'].get('function',{}).get('name'),
             'oracle_reason':p['oracle_reason'],'decision':p['decision'],'reason':p['reason'],
             'blocked':p['blocked'],'executed':p['executed'],
             'backend_effect_count':len(p['backend_effects']),
             'notes_before':p['notes_before'],'notes_after':p['notes_after']}
            for p in raw['proposals']]})
summary['manifest']=json.loads((run/'manifest.json').read_text())
summary['raw_summary_sha256']=hashlib.sha256((run/'summary.json').read_bytes()).hexdigest()
summary['publication_scope']='Counts, run manifest, trial index and allowlisted traces. Raw model messages, transaction evidence, and full backend traces remain local.'
for path in (root/'docs/visuals/model-evaluation-snapshot.json',root/'artifacts/model-eval/latest-public.json'):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(summary,indent=2)+'\n')
print(f"Published {summary['finished_trials']} trial outcomes from {summary['run_id']}")
