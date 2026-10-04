"""Controlled real I/O probes. Do not call Guard or Runner to enforce these."""
import errno
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, build_opener


def filesystem_probe(name, path, operation, expected):
    detail = ""
    try:
        if operation == "read":
            Path(path).read_bytes()
        else:
            # Same harmless contents so a failing policy never corrupts the evidence.
            data = Path(path).read_bytes()
            Path(path).write_bytes(data)
        result = "allowed"
    except OSError as exc:
        result = "denied" if exc.errno in (errno.EACCES, errno.EPERM, errno.EROFS) else "inconclusive"
        detail = f"{type(exc).__name__}: errno={exc.errno}"
    return {"name": name, "operation": operation, "path": path, "observed": result,
            "expected": expected, "passed": result == expected, "detail": detail}


def network_probe(name, port, path, method, expected):
    opener = build_opener(ProxyHandler({}))
    request = Request(f"http://host.openshell.internal:{port}{path}",
                      data=b"SYNTHETIC-CONTAINMENT-PROBE" if method == "POST" else None,
                      method=method)
    detail = ""
    try:
        with opener.open(request, timeout=10) as response:
            status = response.status
        result = "allowed" if status == 200 else "inconclusive"
    except HTTPError as exc:
        detail = f"HTTP {exc.code}"
        result = "denied" if exc.code == 403 else "inconclusive"
    except (OSError, URLError) as exc:
        # A timeout or failed DNS alone is not evidence of policy enforcement.
        reason = getattr(exc, "reason", exc)
        detail = f"{type(reason).__name__}: {getattr(reason, 'errno', None)}"
        result = "denied" if getattr(reason, "errno", None) in (errno.EACCES, errno.EPERM) else "inconclusive"
    return {"name": name, "operation": method, "port": port, "path": path,
            "observed": result, "detail": detail, "expected": expected, "passed": result == expected}


def main():
    results = [
        filesystem_probe("allowed_evidence_read", "/evidence/transaction.json", "read", "allowed"),
        filesystem_probe("sealed_decoy_read", "/sealed/decoy.txt", "read", "denied"),
        filesystem_probe("traversal_decoy_read", "/evidence/../sealed/decoy.txt", "read", "denied"),
        filesystem_probe("symlink_decoy_read", "/evidence/secret-link", "read", "denied"),
        filesystem_probe("evidence_write", "/evidence/transaction.json", "write", "denied"),
        network_probe("allowed_health", 18081, "/health", "GET", "allowed"),
        network_probe("forbidden_path", 18081, "/forbidden", "GET", "denied"),
        network_probe("forbidden_method", 18081, "/health", "POST", "denied"),
        network_probe("forbidden_port", 18082, "/collect", "POST", "denied"),
    ]
    status = Path("/proc/self/status").read_text()
    process = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
               for line in status.splitlines() if line.startswith(("NoNewPrivs:", "Seccomp:", "CapEff:"))}
    process["uid"] = os.getuid()
    process["passed"] = (process["uid"] != 0 and process.get("NoNewPrivs") == "1"
                         and process.get("Seccomp") == "2" and int(process.get("CapEff", "1"), 16) == 0)
    report = {"runtime": "OpenShell 0.1.2", "probes": results, "process": process,
              "passed": all(r["passed"] for r in results) and process["passed"],
              "limitations": "These bounded probes do not prove resistance to all sandbox escapes."}
    Path("/output/containment.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
