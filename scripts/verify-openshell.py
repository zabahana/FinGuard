"""Fail closed unless independent runtime evidence and the agent outcome agree."""
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

root = Path('artifacts/openshell')
read = lambda p: json.loads((root/p).read_text())
probes, report, sandbox = read('output/containment.json'), read('output/report.json'), read('sandbox.json')
events = [json.loads(line) for line in (root/'native-ocsf.jsonl').read_text().splitlines() if line.strip()]
policy = sandbox['policy']
runtime = read('runtime-images.json')
control = read('filesystem-control.json')
workload = next(r for r in runtime if not r['name'].endswith('-supervisor'))
inference = policy['network_policies'].get('local_inference', {})
endpoint = inference.get('endpoints', [{}])[0]
denied = [e for e in events if e.get('action') == 'Denied']
http_denials = {(e.get('http_request',{}).get('http_method'),
                e.get('http_request',{}).get('url',{}).get('path')) for e in denied}
receipts = [json.loads(line) for line in (root/'receiver-run.jsonl').read_text().splitlines() if line.strip()]
checks = {
    'all_io_probes': len(probes['probes']) == 9 and all(p['passed'] for p in probes['probes']),
    'filesystem_control_permits_operations': control['uid'] == probes['process']['uid'] and
        control['sealed_read'] and control['symlink_read'] and control['evidence_write'],
    'nonroot_seccomp_no_capabilities': probes['process']['passed'],
    'real_agent_completed': report['status'] == 'complete' and report['runtime'] == 'NVIDIA OpenShell',
    'sandbox_ready': sandbox['phase'] == 'Ready',
    'landlock_required': policy['landlock']['compatibility'] == 'hard_requirement',
    'test_network_permission_removed': set(policy['network_policies']) == {'local_inference'},
    'inference_only': len(inference.get('endpoints', [])) == 1 and
        endpoint.get('host') == 'host.openshell.internal' and endpoint.get('port') == 11434 and
        endpoint.get('protocol') == 'rest' and endpoint.get('enforcement') == 'enforce' and
        endpoint.get('rules') == [{'allow': {'method': 'POST', 'path': '/api/chat'}}],
    'workload_isolated_from_host': workload['network_mode'] == 'none' and all(
        m['type']=='volume' and m['destination']=='/.openshell/channel' for m in workload['mounts']),
    'enforcement_confirmed_by_supervisor': 'Isolation boundary enforcement confirmed' in (root/'runtime.log').read_text(),
    'native_denial_events': {('GET','/forbidden'),('POST','/health')} <= http_denials and
        any(e.get('dst_endpoint',{}).get('port') == 18082 for e in denied),
    'native_inference_event': any(e.get('action') == 'Allowed' and
        e.get('http_request',{}).get('http_method') == 'POST' and
        e.get('http_request',{}).get('url',{}).get('path') == '/api/chat' for e in events),
    'receiver_saw_only_permitted_request': bool(receipts) and all(
        r['method']=='GET' and r['path']=='/health' and r['port']==18081 for r in receipts),
    'same_runtime': all(e.get('container',{}).get('uid') == sandbox['id'] for e in events),
}
result = {'passed': all(checks.values()), 'checks': checks, 'sandbox_id': sandbox['id'],
          'verified_at': datetime.now(timezone.utc).isoformat(),
          'sandbox_name': sandbox['name'], 'native_ocsf_event_count': len(events),
          'native_denials': len(denied), 'inference_seconds': report['inference_seconds'],
          'scope': 'Local OpenShell software deployment; no Sentry hardware or production bank integration'}
(root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
sys.exit(0 if result['passed'] else 1)
