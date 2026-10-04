"""Publish allowlisted model-evaluation counts and synthetic decision traces."""
import json
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parents[1]
summary=json.loads((root/'artifacts/model-eval/latest.json').read_text())
if not summary['complete'] or summary['phase']!='main':
    raise SystemExit('Only a fully finished main evaluation can be published')
run=root/'artifacts/model-eval'/summary['run_id']
summary['trace_examples']=[]
for cohort in ('single','multi','benign'):
    rows=[t for t in summary['trial_index'] if t['cohort']==cohort]
    rows.sort(key=lambda t:(-t['prohibited_proposals'],t['id']))
    for entry in rows[:3]:
        raw=json.loads((run/f"{entry['id']}.json").read_text())
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
