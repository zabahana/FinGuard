# FinGuard

An agentic banking security research testbed based on `FinGuard.docx`.

Research question: **Can context-aware policies improve financial-agent security beyond static runtime containment?** FinGuard distinguishes enforcement failures from semantic policy failures, where permitted actions violate the intended use of banking data.

## Current implementation

This first milestone is a runnable, dependency-free Python simulation. It provides a fictional bank, a deterministic investigation agent, exact action allowlists, a semantic risk engine, 18 curated scenarios, JSON reports, and redacted JSONL action traces. An optional FastAPI service exposes synthetic banking endpoints.

**This is not OpenShell and is not a security boundary.** No attack executes a host command, reads a host secret, or sends network traffic. Simulated traversal, DNS, symlink and process probes exercise the policy model only. Benchmark results cannot substantiate claims about NVIDIA containment or LLM resistance to prompt injection.

## Run locally

Python 3.10 or newer is sufficient for the CLI and tests. From the repository root:

```sh
python3 -m finguard investigate
python3 -m unittest discover -s tests -v
python3 -m finguard evaluate --mode unrestricted --count 1000 --output artifacts/unrestricted
python3 -m finguard evaluate --mode runtime --count 1000 --output artifacts/runtime
python3 -m finguard evaluate --mode adaptive --count 1000 --output artifacts/adaptive
```

Each evaluation writes `report.json` and `events.jsonl`. The seed controls trace ordering. The 1,000 runs repeat 18 templates; they are not 1,000 unique or statistically independent attacks. Timing varies between runs.

Modes:

- `unrestricted`: all virtual actions execute, establishing a deliberately unsafe baseline.
- `runtime`: exact action allowlists constrain customer scope, file paths, HTTP methods and destinations.
- `adaptive`: runtime controls plus sensitive-content checks and history-based review holds. This layer never broadens runtime permissions.

The example agent investigates C10452, identifies a disputed $8,920 transaction from a new device, and records an analyst recommendation. It cannot initiate a wire transfer or delete a customer.

## Optional synthetic API

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[api]'
.venv/bin/python -m uvicorn finguard.api:app --host 127.0.0.1 --port 8000
```

Interactive endpoint documentation is at `http://127.0.0.1:8000/docs`. The service offers `GET /api/risk-score`, `GET /api/transaction-history`, and `POST /api/case-management`. Reads require `customer_id=C10452`. A case request accepts `{"customer_id":"C10452","text":"Review TX002"}`. Notes are validated only and are not persisted. This local fixture service has no authentication and should remain on loopback. Cross-request history is not tracked by the API; the Runner owns history for each investigation or scenario.

## Project layout

- `finguard/bank.py`: fictional customer records, transactions, complaint, fraud policy and decoy key.
- `finguard/agent.py`: deterministic investigation workflow.
- `finguard/policy.py`: simulated runtime and semantic decisions.
- `finguard/runner.py`: guarded virtual execution and trace generation.
- `finguard/scenarios.py`: six attack families, semantic leakage and legitimate controls.
- `finguard/evaluation.py`: reproducible scheduling and metric denominators.
- `finguard/api.py`: optional FastAPI fixture service.
- `tests/`: behavioral regression tests.
- `docs/RESEARCH_PLAN.md`: requirements, experimental design and remaining milestones.
- `docs/OPENSHELL.md`: real-environment integration requirements.
- `docs/ci-workflow.yml`: GitHub Actions template. CI is not enabled yet; move this file to `.github/workflows/test.yml` and push with a credential that has workflow permission to enable it.

## Interpreting results

Attack deny rate counts only explicit denials. Attack prevention also counts review holds, because review does not execute an action. False block rate counts denied legitimate actions; legitimate review rate is reported separately. Completion requires every step of a legitimate scenario to execute. Exfiltration rate counts executed actions labeled as virtual sensitive-data sinks. Runtime policy violation rate uses independently labeled forbidden steps, not the policy's own decisions, as ground truth.

Decision latency measures the Python policy check only. OpenShell overhead and GPU utilization are `null` until real measurements are available. Reports separate `enforcement_failure`, `semantic_failure` and `held_for_review` outcomes. In unrestricted mode, an `enforcement_failure` label indicates a violated reference policy, not failure of an installed sandbox.

The semantic rules deliberately trade utility for caution. The profile fixture contains an SSN; subsequent outbound actions enter review even when their payload appears harmless. There is no reviewer approval interface yet. Direct SSN matching does not recognize every encoding, and history is only a coarse sensitivity signal. All chained steps are attempted independently; data dependencies are not dynamically propagated.

## Next milestones

1. Integrate a pinned OpenShell release on Linux/Brev and execute real synthetic probes inside its boundary.
2. Add a local Llama/Qwen tool-calling adapter with task-bound sessions and strict action validation.
3. Add PostgreSQL persistence, authenticated API sessions, and auditable human review.
4. Correlate OCSF telemetry, model traces and GPU measurements, then run held-out ablations.

No cloud resources are provisioned by this repository. All included identities, credentials and account data are fictional.
