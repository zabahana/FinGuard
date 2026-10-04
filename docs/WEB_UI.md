# FinGuard security evaluation workspace

The web app presents the security harness: attack coverage, four-way control ablation, model-driven adversarial trials, and separate application/runtime evidence. The Attack Lab and runtime evidence lead the workspace; the real ULB investigation supplies the financial test case. Detector charts and dataset details remain available in the final “Appendix: fraud model” section. The run controls still operate the real ULB and OpenShell workflow. It is separate from the synthetic FastAPI banking fixture. Start it from this checkout:

```sh
.venv/bin/python -m finguard.web
```

Open **http://127.0.0.1:8766**. Use `--port 8767` to choose another port. The server binds only to loopback. It serves a fixed set of UI, diagram, and documentation assets rather than exposing the repository filesystem.

## Before the first run

Install the fraud dependencies using `pip install -e '.[fraud]'` in the project virtual environment. Have Docker Desktop running. Prepare the local Ollama installation and `qwen3:8b` model as described in the README. The service launcher uses the repository's `.local/Ollama.app` and `.local/models` layout; it does not download model weights automatically.

Complete the gateway bootstrap and one-time local registration in [the OpenShell guide](OPENSHELL.md). If the generated gateway config is missing, the service check can run the existing bootstrap, but it does not silently register or replace gateway identities. The current development checkout already has these dependencies and registration.

## Model evaluation

The Model evaluation section shows the expanded 300-trial study with cohort selection, APR/CBR/UER/FBR denominators, prompt-cluster uncertainty, attack-family outcomes, stage exposure, and per-trial seeds. **Run 300 model trials** uses the already-exported evidence and local Qwen model; it does not create a sandbox or test OpenShell runtime enforcement. Prepare the full workflow first. The last completed evaluation remains visible during the new run. See [methodology and limitations](MODEL_EVALUATION.md).

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

## Attack Lab

The **Run Attack Lab** control runs 18 deterministic fixtures in four configurations and three separate Qwen continuations. Mode selection, attack/control filters, and trace inspection show actual saved evidence. Results are separate from the investigation workflow. See [Attack Lab methodology](ATTACK_LAB.md) for baseline qualifications, evidence attribution, and runtime cleanup.
