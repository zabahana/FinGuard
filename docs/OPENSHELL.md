# FinGuard with NVIDIA OpenShell

FinGuard now has a tested local integration with **OpenShell 0.1.2**, the software runtime component of NVIDIA Open Agent Safety Platform. It runs on this Apple Silicon Mac through Docker Desktop. Sentry's BlueField hardware watchdog is not installed or emulated.

The original Python Guard remains an application policy layer. The new path additionally runs the agent in OpenShell's separate workload container, controlled by an authenticated gateway and supervisor. Use the commands below: running the old Python CLI directly on macOS does not put it inside OpenShell.

## What is running

- Gateway: local mTLS endpoint `https://localhost:17670`, with operator state in ignored `.local/openshell/`.
- Verified sandbox: `finguard-verified`, under the restricted deployment policy.
- Model: local Qwen3 8B through Ollama on the Mac GPU. Only `POST /api/chat` on the trusted host at port 11434 is permitted.
- Evidence: one exported held-out ULB transaction and its trained detector score. Raw CSV, labels, model weights, repository secrets and gateway credentials are not copied into the sandbox.
- Files: agent code and evidence are read-only. Output and temporary directories are writable. Landlock is a hard startup requirement.
- Process: UID/GID 1000, no effective capabilities, no-new-privileges, and an active seccomp filter. This does not prohibit every subprocess or interpreter command.
- Actions: real inference and real OS/network containment. Case submission remains simulated; no real bank API is connected.

The detector runs on the trusted host and exports its score before sandbox creation. Qwen runs its tool-calling loop inside the sandbox and calls the host inference service. This is pretrained inference, not model training inside OpenShell.

## Use the existing sandbox

From the repository root:

```sh
sh scripts/investigate-openshell.sh
```

This runs another investigation in `finguard-verified`, collects native logs, and rechecks its deployment evidence. It replaces the current `artifacts/openshell/` reports. The supplied case remains fixed until a new image is prepared.

## Restart local services

Docker Desktop must be running. Start these in separate terminals when needed:

```sh
sh scripts/serve-model.sh
sh scripts/start-openshell.sh
```

The gateway startup uses `.local/openshell/gateway.toml`. This is generated from the committed template and contains this Mac's Docker socket and bridge IP. No system-wide installation, Docker networking preference change, or unauthenticated gateway is required for the verified configuration.

## Rebuild and test a fresh sandbox

For a fresh Mac checkout, first follow `ULB.md` to obtain the dataset and train the detector, and install/run Ollama. Docker Desktop is a prerequisite.

```sh
.venv/bin/python scripts/setup-openshell.py
```

The bootstrap verifies pinned release archives, prepares local mTLS certificates and generates the Docker configuration. It is currently specific to Apple Silicon macOS. Start the gateway using the command above, then register it once:

```sh
. scripts/openshell-env.sh
openshell gateway add https://localhost:17670 --local --name openshell
openshell status
```

If already registered, use `openshell status`; registration is not repeated. Start the controlled test receivers in another terminal:

```sh
.venv/bin/python scripts/containment-receiver.py
```

Then run the full test-to-deployment workflow:

```sh
sh scripts/run-openshell.sh
```

An optional argument selects a new unique sandbox name. The workflow refuses to replace an existing sandbox. It prepares a minimal build context, builds the image, launches with a test policy, enables native OCSF JSON export, waits for observed activation, runs real containment probes, removes the test-only network permission, waits for that policy to load, and runs Qwen under the deployment policy. Failures stop the script; they do not relax enforcement. A fresh run creates a new sandbox and replaces the local collected reports, so archive results beforehand if needed.

The test receiver listens only on loopback ports 18081 and 18082, records method/path/port, and never saves submitted payloads. Stop it with Ctrl+C when testing is finished. It is unnecessary for normal investigations.

## Independent verification

The nine I/O checks are executed directly by Python inside the sandbox, with no calls to FinGuard's Guard or Runner:

- An allowed evidence read succeeds.
- Direct, traversal and symlink reads of a synthetic decoy are denied.
- Writing the evidence file is denied.
- An allowed health request succeeds.
- A forbidden HTTP path, HTTP method and network port are denied.

Non-root identity, empty capabilities, no-new-privileges and seccomp mode are checked separately. A plain Docker control run confirmed that the decoy is otherwise readable and the evidence file writable by the same UID, so ordinary file permissions do not explain the filesystem denials. Timeouts and DNS failures are classified as inconclusive, never as successful enforcement.

Native supervisor OCSF events independently confirm HTTP and port denials, and the controlled receiver sees only the allowed request. The deployment gate checks these alongside the completed real-data investigation, active sandbox, required Landlock setting and absence of the test network rule.

OpenShell adds baseline filesystem paths, including `/proc`, `/var/log`, `/dev/urandom`, and `/dev/null`, when it composes an effective network policy. The collected effective policy records these additions; the YAML input alone is not the complete enforcement configuration.

## Collected evidence

`artifacts/openshell/` contains:

- `verification.json`: timestamped gate result and bounded verification scope.
- `output/containment.json`: actual I/O outcomes and process flags.
- `filesystem-control.json`: same-UID control results without OpenShell.
- `output/report.json`: Qwen's real-data investigation.
- `output/events.jsonl`: FinGuard application events, not OCSF.
- `native-ocsf.jsonl`: unmodified native supervisor OCSF JSON records.
- `runtime.log`: human-readable OpenShell logs.
- `sandbox.json` and `effective-policy.json`: runtime identity, configuration and composed policy.
- `runtime-images.json`: actual image IDs, network modes and mount destinations.
- `receiver-run.jsonl`: receiver observations for the tested probe run.

In OpenShell 0.1.2's Docker driver, audit files live on the supervisor's private `/var/log` tmpfs, not in the workload. The official supervisor image contains no shell. The collector uses a temporary, same-UID container with no network, no capabilities and no-new-privileges to read only those native logs through the supervisor PID namespace. This is an operator collection action; the agent never receives supervisor access. Logs must be collected before deleting/stopping the supervisor because its tmpfs is ephemeral.

The CLI/gateway/prover archives are pinned with SHA-256 checksums in `setup-openshell.py`. The Python base and NVIDIA sandbox/supervisor images are pinned by digest in the Dockerfile and gateway template. The generated runtime image IDs are captured with each collection.

## Scope and remaining work

This is a verified **local OpenShell software deployment**, not a completed enterprise deployment of the entire NVIDIA platform. It does not include Sentry/BlueField hardware, a bank connection, authenticated case persistence, a production identity provider, a SIEM ingestion pipeline, or continuous red-team evaluation. The probe set cannot prove protection against every sandbox escape or prompt injection. Sensitive-content and business-purpose checks remain application-level controls and are not substitutes for service-side authorization when real banking APIs are introduced.

The Mac and Docker administrator are trusted. A host administrator can stop the gateway or replace images. Generated notes are not guaranteed factually correct just because an action was allowed. The allowed local inference channel can carry evidence to Ollama, which must remain configured with cloud inference disabled.

To inspect or stop the deployed sandbox:

```sh
. scripts/openshell-env.sh
openshell sandbox get finguard-verified
openshell sandbox stop finguard-verified
# Resume the stopped sandbox:
openshell sandbox start finguard-verified
```

If Docker's bridge IP changes, the bootstrap fails with an explicit certificate mismatch instead of disabling TLS verification. Stop the FinGuard gateway and regenerate its matching local configuration and certificates before retrying.

## References

- [NVIDIA Open Agent Safety Platform](https://nvidianews.nvidia.com/news/open-agent-safety-platform)
- [OpenShell v0.1.2 release](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.2)
- [Installation](https://docs.nvidia.com/openshell/latest/about/installation/)
- [Policy schema](https://docs.nvidia.com/openshell/latest/how-it-works/policies/schema)
- [Docker runtime configuration](https://docs.nvidia.com/openshell/latest/how-it-works/gateways/configuration)
- [Native OCSF JSON export](https://docs.nvidia.com/openshell/latest/observability/ocsf-json-export)
