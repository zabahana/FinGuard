"""Loopback-only operator UI for the real FinGuard pipeline.

Not the synthetic banking API. Jobs run fixed repository commands on the trusted
host; the real investigation itself still executes through OpenShell.
"""
import argparse
import copy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STAGES = {
    "download": "Prepare real ULB data", "train": "Train and evaluate detector",
    "services": "Check local services", "export": "Export label-blind evidence",
    "build": "Build minimal agent image", "control": "Run plain Docker control",
    "sandbox": "Create sandbox and enable audit", "probes": "Run containment probes",
    "policy": "Apply deployment policy", "investigate": "Run Qwen investigation",
    "collect": "Collect native and application evidence", "verify": "Verify local deployment",
    "attacks": "Run bounded four-way Attack Lab",
    "model_eval": "Run 300 model-security trials",
}
ACTIONS = {"download", "train", "services", "investigate", "full", "attacks", "model_eval"}


def now():
    return datetime.now(timezone.utc).isoformat()


def sandbox_name():
    # OpenShell 0.1.2 limits sandbox names to 19 characters.
    return "fgw-" + datetime.now().strftime("%m%d%H%M%S") + secrets.token_hex(2)


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def environment():
    local = ROOT / ".local/openshell"
    return dict(os.environ, PYTHONUNBUFFERED="1", NO_COLOR="1",
                XDG_CONFIG_HOME=str(local / "config"), XDG_STATE_HOME=str(local / "state"),
                OPENSHELL_LOCAL_TLS_DIR=str(local / "tls-desktop"),
                PATH=str(local) + os.pathsep + os.environ.get("PATH", ""))


class JobManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.job = None
        self.history = []
        self.children = []
        # Keep the last published snapshot across restarts, including failed jobs.
        self.result = read_json(ROOT / "artifacts/web/published-results.json") or self.read_results()
        lab = read_json(ROOT / "artifacts/attack-lab/latest.json")
        if lab is not None:
            self.result.setdefault("attack_lab", lab)
        evaluation = read_json(ROOT / "artifacts/model-eval/latest-public.json")
        if evaluation is not None:
            self.result["model_eval"] = evaluation

    def read_results(self):
        # Explicitly serve only these report types, never native logs or credentials.
        mapping = {"training": "ulb/training_report.json", "agent": "openshell/output/report.json",
                   "verification": "openshell/verification.json", "containment": "openshell/output/containment.json",
                   "attack_lab": "attack-lab/latest.json", "model_eval": "model-eval/latest-public.json"}
        return {key: read_json(ROOT / "artifacts" / path) for key, path in mapping.items()}

    def state(self):
        with self.lock:
            return {"job": copy.deepcopy(self.job), "history": copy.deepcopy(self.history[-8:]),
                    "results": copy.deepcopy(self.result), "stages": STAGES,
                    "readiness": {"dataset": (ROOT / ".local/datasets/ulb/creditcard.csv").exists(),
                                  "detector": (ROOT / "artifacts/ulb/model.joblib").exists(),
                                  "ollama_port": port_open(11434), "gateway_port": port_open(17670)},
                    "scope": "Local operator app. Real data and inference; banking actions simulated."}

    def start(self, action):
        if action not in ACTIONS:
            raise ValueError("Unknown workflow action")
        with self.lock:
            if self.job and self.job["status"] == "running":
                raise RuntimeError("A job is already running; wait for it to finish")
            job_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)
            self.job = {"id": job_id, "action": action, "status": "running", "started_at": now(),
                        "finished_at": None, "steps": [], "logs": [], "error": None,
                        "sandbox": None}
            threading.Thread(target=self.run, args=(self.job,), daemon=True).start()
            return copy.deepcopy(self.job)

    def log(self, job, text):
        # Strip terminal control sequences; keep UI/log size bounded.
        text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text).rstrip()[:4000]
        with self.lock:
            job["logs"].append(text)
            del job["logs"][:-250]

    def stage(self, job, name):
        if name not in STAGES:
            return
        with self.lock:
            for step in job["steps"]:
                if step["status"] == "running":
                    step.update(status="complete", finished_at=now())
            job["steps"].append({"id": name, "title": STAGES[name], "status": "running", "started_at": now()})

    def command(self, job, args, timeout=1800):
        self.log(job, "$ " + " ".join(str(arg) for arg in args))
        proc = subprocess.Popen(args, cwd=ROOT, env=environment(), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, start_new_session=True)
        timed_out = threading.Event()

        def expire():
            timed_out.set()
            # Only the process group created by this job command is terminated.
            import signal
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        timer = threading.Timer(timeout, expire)
        timer.start()
        try:
            for line in proc.stdout:
                self.log(job, line)
                if line.startswith("FINGUARD_STAGE:"):
                    self.stage(job, line.strip().split(":", 1)[1])
            code = proc.wait()
            if timed_out.is_set():
                raise RuntimeError(f"Command exceeded {timeout} seconds; inspect retained evidence")
            if code:
                raise RuntimeError(f"Command exited with status {code}; see job log")
        finally:
            timer.cancel()
            proc.stdout.close()

    def service(self, job, command, port, name):
        if port_open(port):
            self.log(job, f"{name}: existing listener detected; checking service identity next")
            return
        directory = ROOT / "artifacts/web/services"
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / f"{name}.log").open("a") as stream:
            proc = subprocess.Popen(command, cwd=ROOT, env=environment(), stdout=stream,
                                    stderr=subprocess.STDOUT, start_new_session=True)
        self.children.append(proc)
        for _ in range(60):
            if proc.poll() is not None:
                raise RuntimeError(f"{name} failed to start; inspect artifacts/web/services/{name}.log")
            if port_open(port):
                self.log(job, f"{name}: started local service")
                return
            time.sleep(0.5)
        proc.terminate()
        raise RuntimeError(f"{name} did not become ready in 30 seconds")

    def ensure_services(self, job):
        self.stage(job, "services")
        self.command(job, ["docker", "info", "--format", "{{.ServerVersion}}"], timeout=30)
        self.service(job, ["sh", "scripts/serve-model.sh"], 11434, "ollama")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:11434/api/tags", timeout=10) as response:
            models = json.load(response).get("models", [])
        if not any(model.get("name") == "qwen3:8b" for model in models):
            raise RuntimeError("qwen3:8b is not installed in Ollama. Follow docs/WEB_UI.md to prepare the model.")
        if not (ROOT / ".local/openshell/gateway.toml").exists():
            self.command(job, [sys.executable, "scripts/setup-openshell.py"])
        self.service(job, ["sh", "scripts/start-openshell.sh"], 17670, "gateway")
        # This intentionally does not reconfigure or take over a different gateway.
        self.command(job, [str(ROOT / ".local/openshell/openshell"), "status"], timeout=30)

    def archive(self, job):
        directory = ROOT / "artifacts/web/jobs" / job["id"]
        directory.mkdir(parents=True, exist_ok=True)
        current = ROOT / "artifacts/openshell"
        if current.exists():
            shutil.copytree(current, directory / "previous-openshell")
        (directory / "previous-results.json").write_text(json.dumps(self.result, indent=2) + "\n")
        return directory

    def receiver(self, job):
        # Reuse only a responding controlled receiver, never kill a pre-existing listener.
        ports = (18081, 18082)
        existing = [port_open(port) for port in ports]
        proc = None
        if any(existing) and not all(existing):
            raise RuntimeError("Only one test receiver port is available; stop the conflicting listener first")
        if not any(existing):
            proc = subprocess.Popen([sys.executable, "scripts/containment-receiver.py"], cwd=ROOT,
                                    env=environment(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(40):
                if all(port_open(port) for port in ports):
                    break
                if proc.poll() is not None:
                    raise RuntimeError("Controlled receiver could not start")
                time.sleep(.1)
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for port in ports:
                with opener.open(f"http://127.0.0.1:{port}/health", timeout=3) as response:
                    if json.load(response) != {"controlled_receiver": True}:
                        raise RuntimeError("A test port belongs to an unexpected service")
        except Exception:
            if proc:
                proc.terminate()
                proc.wait(timeout=5)
            raise
        return proc

    def run(self, job):
        directory = None
        receiver = None
        outcome = "failed"
        try:
            directory = self.archive(job)
            action = job["action"]
            if action in {"download", "full"}:
                self.stage(job, "download")
                # The downloader verifies an existing file instead of downloading it again.
                self.command(job, [sys.executable, "scripts/download-ulb.py"])
            if action in {"train", "full"}:
                self.stage(job, "train")
                self.command(job, [sys.executable, "-m", "finguard", "train-fraud"])
            if action in {"services", "investigate", "full", "attacks"}:
                self.ensure_services(job)
            if action == "model_eval":
                self.stage(job, "model_eval")
                self.command(job, [sys.executable, "-m", "finguard.model_eval", "--phase", "main"], timeout=7200)
                self.command(job, [sys.executable, "scripts/publish-model-eval.py"])
            if action == "attacks":
                self.stage(job, "attacks")
                self.command(job, ["sh", "scripts/run-attack-lab.sh"], timeout=1800)
            if action == "full":
                job["sandbox"] = sandbox_name()
                receiver = self.receiver(job)
                self.command(job, ["sh", "scripts/run-openshell.sh", job["sandbox"]])
            elif action == "investigate":
                verification = self.result.get("verification") or {}
                name = verification.get("sandbox_name", "finguard-verified")
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", name):
                    raise RuntimeError("Invalid recorded sandbox name")
                job["sandbox"] = name
                self.stage(job, "investigate")
                self.command(job, ["sh", "scripts/investigate-openshell.sh", name])
            with self.lock:
                # Publish report types touched by this job; never combine a partial failed
                # run's agent report with the previous successful verification in the UI.
                fresh = self.read_results()
                keys = {"train": ["training"], "full": list(fresh),
                        "investigate": ["agent", "verification", "containment"],
                        "attacks": ["attack_lab"], "model_eval": ["model_eval"]}.get(action, [])
                for key in keys:
                    self.result[key] = fresh[key]
                outcome = "complete"
        except Exception as exc:
            with self.lock:
                job["error"] = str(exc)
            self.log(job, "ERROR: " + str(exc))
        finally:
            if receiver:
                receiver.terminate()
                receiver.wait(timeout=5)
            with self.lock:
                job["status"] = outcome
                for step in job["steps"]:
                    if step["status"] == "running":
                        step.update(status="complete" if job["status"] == "complete" else "failed", finished_at=now())
                job["finished_at"] = now()
                self.history.append({key: job[key] for key in ("id", "action", "status", "started_at", "finished_at", "sandbox", "error")})
                if directory:
                    (directory / "job.json").write_text(json.dumps(job, indent=2) + "\n")
                    (directory / "results.json").write_text(json.dumps(self.result, indent=2) + "\n")
                    published = ROOT / "artifacts/web/published-results.json"
                    temporary = published.with_suffix(".tmp")
                    temporary.write_text(json.dumps(self.result, indent=2) + "\n")
                    temporary.replace(published)


class WebServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, manager=None):
        self.manager = manager or JobManager()
        self.token = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def permitted(self):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        origin = self.headers.get("Origin")
        return (self.headers.get("Host") in hosts and
                (origin is None or origin in {f"http://{host}" for host in hosts}) and
                self.headers.get("Sec-Fetch-Site") not in {"cross-site", "same-site"})

    def respond(self, status, data, content_type="application/json"):
        body = json.dumps(data).encode() if content_type == "application/json" else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.permitted():
            return self.respond(403, {"error": "Only local same-origin requests are accepted"})
        path = urlsplit(self.path).path
        if path == "/api/state":
            return self.respond(200, dict(self.server.manager.state(), token=self.server.token))
        files = {"/": ROOT / "finguard/web_static/index.html",
                 "/app.js": ROOT / "finguard/web_static/app.js",
                 "/style.css": ROOT / "finguard/web_static/style.css"}
        for name in ("components", "end-to-end", "investigation", "deployment"):
            for extension in ("svg", "png"):
                files[f"/assets/{name}.{extension}"] = ROOT / f"docs/assets/{name}.{extension}"
            files[f"/diagrams/{name}.mmd"] = ROOT / f"docs/diagrams/{name}.mmd"
        for name in ("MEDIUM_ARTICLE.md", "WEB_UI.md", "OPENSHELL.md", "ULB.md", "ARCHITECTURE.md"):
            files[f"/docs/{name}"] = ROOT / "docs" / name
        target = files.get(path)
        if target is None or not target.is_file():
            return self.respond(404, {"error": "Not found"})
        mime = mimetypes.guess_type(str(target))[0] or "text/plain"
        self.respond(200, target.read_bytes(), mime + ("; charset=utf-8" if mime.startswith("text/") else ""))

    def do_POST(self):
        if not self.permitted() or not secrets.compare_digest(self.headers.get("X-FinGuard-Token", ""), self.server.token):
            return self.respond(403, {"error": "Missing local session token or invalid origin"})
        if self.path != "/api/jobs":
            return self.respond(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024 or self.headers.get("Content-Type") != "application/json":
                raise ValueError("Expected a small JSON request")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict) or set(body) != {"action"} or not isinstance(body["action"], str):
                raise ValueError("Only the action field is accepted")
            self.respond(202, self.server.manager.start(body["action"]))
        except (ValueError, json.JSONDecodeError) as exc:
            self.respond(400, {"error": str(exc)})
        except RuntimeError as exc:
            self.respond(409, {"error": str(exc)})


def main():
    parser = argparse.ArgumentParser(description="FinGuard local operator web UI")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = WebServer(args.port)
    print(f"FinGuard UI: http://127.0.0.1:{server.server_port}", flush=True)
    print("Local operator access only. Keep this process running until active jobs finish.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
