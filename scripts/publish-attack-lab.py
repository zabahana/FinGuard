"""Export bounded Attack Lab observations for publication, without raw model evidence."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=root/'artifacts/attack-lab/latest.json'
report=json.loads(source.read_text())
snapshot={'created_at':report['created_at'],'passed':report['passed'],'scope':report['scope'],
          'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'modes':{}}
for name,mode in report['modes'].items():
    snapshot['modes'][name]={'passed':mode['passed'],'receiver_check':mode['receiver_check'],'cases':[
        {key:case[key] for key in ('id','family','attack','expected','observed','passed','layer','detail',
            'native_evidence','native_events','application_events','invalid_tool_calls','workflow_status') if key in case}
        for case in mode['cases']]}
snapshot['prompt_trials']=[{key:trial.get(key) for key in ('id','instruction','proposed_calls','outcome','runtime_attack_attempted')}
    for trial in report['modes']['both']['prompt_injection']['trials']]
(root/'docs/visuals/attack-lab-snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
print('Published bounded Attack Lab snapshot with source digest')
