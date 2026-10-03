"""Install pinned OpenShell tools and prepare an authenticated local Mac gateway."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1]
os.chdir(root)
if platform.system() != 'Darwin' or platform.machine() != 'arm64':
    raise SystemExit('This bootstrap is for Apple Silicon macOS with Docker Desktop.')
local = root / '.local/openshell'
local.mkdir(parents=True, exist_ok=True)
checksums = {
    'openshell': 'cdde7e92bd7eac664031cf171cfe80d29e7f122a6674917b25a4ce0bcbc33466',
    'openshell-gateway': '640068efa16e446d5f4f9ffaec0af769dbab04d686473d2a7bd6bafeb4ef7f45',
    'openshell-prover': '77f624498e1110abd0da26e926a71c834b5e58f8baa5a33252d59d7ab4629a53',
}
for package, digest in checksums.items():
    archive = local / f'{package}-aarch64-apple-darwin.tar.gz'
    if not archive.exists():
        urllib.request.urlretrieve('https://github.com/NVIDIA/OpenShell/releases/download/v0.1.2/'+archive.name, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
        raise SystemExit(f'Checksum mismatch: {archive.name}')
    # Validate an existing installation against the verified release archive.
    with tarfile.open(archive) as tar:
        member = next(m for m in tar.getmembers() if Path(m.name).name == package and m.isfile())
        expected_binary = tar.extractfile(member).read()
    binary = local / package
    if not binary.exists() or binary.read_bytes() != expected_binary:
        binary.write_bytes(expected_binary)
        binary.chmod(0o755)

subprocess.run(['docker','info'], check=True, stdout=subprocess.DEVNULL)
base_image = 'python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3'
bridge = subprocess.check_output(['docker','run','--rm',base_image,'python','-c',
    'import socket; print(socket.gethostbyname("host.docker.internal"))'],text=True).strip()
ipaddress.ip_address(bridge)
endpoint = subprocess.check_output(['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'],text=True).strip()
if not endpoint.startswith('unix://'):
    raise SystemExit('Expected a local Docker Desktop Unix socket, not a remote engine.')
env = dict(os.environ, XDG_CONFIG_HOME=str(local/'config'), XDG_STATE_HOME=str(local/'state'),
           OPENSHELL_LOCAL_TLS_DIR=str(local/'tls-desktop'))
cert = local/'tls-desktop/server/tls.crt'
if cert.exists():
    description = subprocess.check_output(['openssl','x509','-in',str(cert),'-noout','-text'],text=True)
    if f'IP Address:{bridge}' not in description:
        raise SystemExit('Docker bridge IP changed. Stop the gateway and regenerate its local TLS bundle before continuing.')
else:
    subprocess.run([str(local/'openshell-gateway'),'generate-certs','--output-dir',str(local/'tls-desktop'),
                    '--server-san','host.openshell.internal','--server-san','host.docker.internal',
                    '--server-san',bridge],env=env,check=True)
configuration = (root/'integration/openshell/gateway.toml').read_text()
configuration += f'socket_path = {json.dumps(endpoint[7:])}\ngrpc_endpoint = "https://{bridge}:17670"\n'
(local/'gateway.toml').write_text(configuration)
subprocess.run([str(local/'openshell-gateway'),'config','preflight','--path',str(local/'gateway.toml')],env=env,check=True)
print('OpenShell 0.1.2 verified. Start: sh scripts/start-openshell.sh')
