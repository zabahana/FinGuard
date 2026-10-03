# FinGuard local web workspace

The web app operates the real ULB and OpenShell workflow. It is separate from the synthetic FastAPI banking fixture. Start it from this checkout:

```sh
.venv/bin/python -m finguard.web
```

Open **http://127.0.0.1:8766**. Use `--port 8767` to choose another port. The server binds only to loopback. It serves a fixed set of UI, diagram, and documentation assets rather than exposing the repository filesystem.

## Before the first run

Install the fraud dependencies using `pip install -e '.[fraud]'` in the project virtual environment. Have Docker Desktop running. Prepare the local Ollama installation and `qwen3:8b` model as described in the README. The service launcher uses the repository's `.local/Ollama.app` and `.local/models` layout; it does not download model weights automatically.

Complete the gateway bootstrap and one-time local registration in [the OpenShell guide](OPENSHELL.md). If the generated gateway config is missing, the service check can run the existing bootstrap, but it does not silently register or replace gateway identities. The current development checkout already has these dependencies and registration.

## Run controls

- **Prepare data** downloads or verifies the checksum-pinned real ULB CSV.
- **Train detector** runs the real chronological training and evaluation pipeline, replacing `artifacts/ulb/` outputs.
- **Start / check services** verifies Docker, starts missing project-local Ollama and gateway services, checks the installed model and calls the authenticated OpenShell status command. Listener indicators alone are not service identity or security checks.
- **Rerun sandbox investigation** uses the last published sandbox name. It runs Qwen, collects reports and checks verification. It reuses the sandbox's existing evidence and earlier containment probes.
- **Run full workflow** prepares data, retrains, starts/checks services, creates a uniquely named sandbox, runs the plain Docker control and nine real probes, narrows policy, runs Qwen, collects evidence, and evaluates the gate.

The UI shows actual command output and stage transitions, not simulated progress percentages. It allows one job at a time per server process. Run only one operator server and avoid running the CLI pipeline concurrently because both write the same artifact directories. There is no cancellation button; wait for a job to finish before closing the server. Commands have bounded timeouts, but a failed run can leave a sandbox for inspection.

Previous OpenShell artifacts are copied to `artifacts/web/jobs/JOB_ID/previous-openshell/` before each job. The job record and published result snapshot are saved alongside them. The UI retains the previous published results if a job fails; inspect the error and job log rather than interpreting old results as a new success. History shown in the UI is for the current server session; saved files remain after restart.

Services started by the UI remain running for subsequent investigations. A controlled test receiver started by a full job is stopped afterward. Pre-existing listeners are not stopped. Each full run leaves a fresh sandbox available; use the OpenShell CLI to stop sandboxes no longer needed. The UI does not automatically delete evidence or sandboxes.

## Reading the visualizations

Detector precision, recall, average precision, confusion counts, and partition sizes come from the training report. The recommendation, score and tool counts come from the agent report. The containment and verification panels come from independent probe and gate reports. Saved timestamps distinguish these measurements. Running a new training job does not change evidence already baked into an existing sandbox image.

The architecture tab offers four Mermaid-rendered diagrams with downloadable SVG, PNG, and editable `.mmd` sources. The [offline visual guide](visual-guide.html) and [Medium draft](MEDIUM_ARTICLE.md) remain separate publication artifacts; update those using `scripts/build-visual-guide.py` after selecting a final run.

## Access boundary

This is a trusted local operator tool, not a remotely authenticated service. Job requests accept only named actions, not arbitrary commands or paths. Mutating requests require a per-server token and same-origin checks; Host validation also blocks unrelated hostnames. No cross-origin API access is enabled. Do not expose the port through a tunnel or reverse proxy.

The UI and pipeline controller run on the trusted Mac. Only the contained investigation runs inside OpenShell. Banking actions remain simulated. A passing verification gate covers the recorded checks, not universal agent safety.
