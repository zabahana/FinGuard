"""Four-way bounded control ablation, with separate artifacts and native evidence."""
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from finguard.web import JobManager, sandbox_name

root=Path('artifacts/attack-lab')/datetime.now().strftime('%Y%m%d-%H%M%S')
root.mkdir(parents=True)
def run(*args):
    subprocess.run(args,check=True)
def output(*args):
    return subprocess.check_output(args,text=True)
manager=JobManager()
receiver=None
modes={}
try:
    receiver=manager.receiver({})
    run(sys.executable,'scripts/prepare-openshell.py')
    run('docker','build','-t','finguard-attack-lab:0.1.2','.local/openshell/build')
    for mode in ('unguarded','finguard','openshell','both'):
        print('ATTACK_LAB_MODE:'+mode,flush=True)
        directory=root/mode
        directory.mkdir()
        receiver_log=Path('artifacts/openshell/receiver.jsonl')
        offset=len(receiver_log.read_text().splitlines())
        if mode in ('unguarded','finguard'):
            raw=output('docker','run','--rm','--add-host','host.openshell.internal:host-gateway',
                       'finguard-attack-lab:0.1.2','python','-m','finguard.attack_lab','--mode',mode)
            report=json.loads(raw)
        else:
            name=sandbox_name()
            run('openshell','sandbox','create','--name',name,'--from','finguard-attack-lab:0.1.2',
                '--policy','integration/openshell/test-policy.yaml','--cpu','2','--memory','512Mi',
                '--approval-mode','manual','--no-auto-providers','--detach','--','/bin/sleep','infinity')
            try:
                run('openshell','settings','set',name,'--key','ocsf_json_enabled','--value','true')
                for _ in range(30):
                    if 'OCSF JSONL logging toggled' in output('openshell','logs',name,'-n','100'):
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError('Native audit export did not activate')
                args=['openshell','sandbox','exec','--name',name,'--no-login-shell','--workdir','/opt/finguard',
                      '--','python','-m','finguard.attack_lab','--mode',mode]
                if mode=='both': args.append('--injections')
                run(*args)
                run(sys.executable,'scripts/collect-openshell.py',name,str(directory))
                report=json.loads((directory/'output/attack-lab.json').read_text())
                native=[json.loads(line) for line in (directory/'native-ocsf.jsonl').read_text().splitlines()]
                for case in report['cases']:
                    if case['family']=='network':
                        matches=[i+1 for i,e in enumerate(native) if e.get('dst_endpoint',{}).get('port')==case['port']
                                 and e.get('action')==('Denied' if case['observed']=='denied' else 'Allowed')
                                 and (case['id']=='forbidden_port' or (e.get('http_request',{}).get('http_method')==case['operation']
                                      and e.get('http_request',{}).get('url',{}).get('path')==case['path']))]
                        case['native_evidence']={'file':str(directory/'native-ocsf.jsonl'),'lines':matches}
                        case['native_events']=[{key:native[i-1].get(key) for key in
                            ('action','time','http_request','dst_endpoint','container')} for i in matches]
                        if case['attack'] and not matches: case['passed']=False
                report['sandbox_name']=name
                report['native_event_count']=len(native)
            finally:
                run('openshell','sandbox','stop',name)
        receipts=[json.loads(line) for line in receiver_log.read_text().splitlines()[offset:]]
        (directory/'receiver.json').write_text(json.dumps(receipts,indent=2)+'\n')
        expected_receipts=1 if mode in ('openshell','both') else 4
        report['receiver_check']=(len(receipts)==expected_receipts and
            (mode in ('unguarded','finguard') or all(r['port']==18081 and r['method']=='GET' and r['path']=='/health' for r in receipts)))
        report['passed']=all(c['passed'] for c in report['cases']) and report['receiver_check']
        (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        modes[mode]=report
    summary={'created_at':datetime.now(timezone.utc).isoformat(),'artifact_directory':str(root),'modes':modes,
             'passed':all(m['passed'] for m in modes.values()),
             'scope':'18 deterministic fixtures x 4 configurations, plus 3 model continuation trials in combined mode. Synthetic decoys and controlled local sinks only. No certification or universal security claim.'}
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    Path('artifacts/attack-lab/latest.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'passed':summary['passed'],'artifacts':str(root)},indent=2))
    if not summary['passed']: raise SystemExit(1)
finally:
    if receiver:
        receiver.terminate()
        receiver.wait(timeout=5)
