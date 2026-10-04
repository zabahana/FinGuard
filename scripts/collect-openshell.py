"""Collect native supervisor logs without exposing the supervisor state to the agent."""
import json
from pathlib import Path
import subprocess
import sys

name = sys.argv[1] if len(sys.argv) > 1 else 'finguard-ulb'
root = Path(sys.argv[2] if len(sys.argv) > 2 else 'artifacts/openshell')
root.mkdir(parents=True, exist_ok=True)
def run(*args):
    return subprocess.check_output(args, text=True)
metadata = json.loads(run('openshell', 'sandbox', 'get', name, '-o', 'json'))
(root/'sandbox.json').write_text(json.dumps(metadata, indent=2)+'\n')
(root/'effective-policy.json').write_text(run('openshell','policy','get',name,'--full','-o','json'))
(root/'runtime.log').write_text(run('openshell','logs',name,'-n','1000'))
containers = run('docker', 'ps', '--format', '{{.Names}}').splitlines()
matching = [n for n in containers if metadata['id'] in n and n.endswith('-supervisor')]
if len(matching) != 1:
    raise SystemExit('Cannot identify the sandbox supervisor uniquely')
runtime = []
for container in (matching[0], matching[0].removesuffix('-supervisor')):
    details = json.loads(run('docker','inspect',container))[0]
    runtime.append({'name': container, 'image_id': details['Image'],
                    'network_mode': details['HostConfig']['NetworkMode'],
                    'user': details['Config']['User'],
                    'mounts': [{'type': m['Type'], 'destination': m['Destination'], 'writable': m['RW']}
                               for m in details['Mounts']]})
(root/'runtime-images.json').write_text(json.dumps(runtime,indent=2)+'\n')
# The official supervisor image contains no shell. Docker cp sees its rootfs,
# not the tmpfs audit sink. A same-UID, no-network collector reads only native logs.
code = ('from pathlib import Path; import sys; '
        '[sys.stdout.write(p.read_text()) for p in sorted(Path("/proc/1/root/var/log").glob("openshell-ocsf.*.log"))]')
raw = run('docker','run','--rm','--network','none','--pid=container:'+matching[0],
          '--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges',
          'python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3',
          'python','-c',code)
rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
if not rows or any(r.get('metadata',{}).get('product',{}).get('name') != 'OpenShell Sandbox Supervisor'
                   or r.get('container',{}).get('uid') != metadata['id'] for r in rows):
    raise SystemExit('Native NVIDIA OCSF events are missing or invalid')
(root/'native-ocsf.jsonl').write_text(raw)
subprocess.run(['openshell','sandbox','download',name,'/output',str(root/'output')], check=True)
print(f'Collected {len(rows)} native OCSF events from {name}')
