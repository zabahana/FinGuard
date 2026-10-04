# FinGuard

An experimental security harness for evaluating layered controls around tool-using financial AI agents. FinGuard separates application authorization from runtime capability enforcement and tests both through deterministic attacks, control ablation, model-driven adversarial instructions, and independently observable audit evidence.

The real-data fraud investigation is the financial test case used to exercise the architecture. Start with the [Attack Lab methodology and results](docs/ATTACK_LAB.md); detector development and performance are supporting context in [the article appendix](docs/MEDIUM_ARTICLE.md#appendix-a).

Research question: **Can context-aware policies improve financial-agent security beyond static runtime containment?** FinGuard distinguishes enforcement failures from semantic policy failures, where permitted actions violate the intended use of banking data.

For data, model, runtime, and documentation-tool provenance, see [Sources and references](docs/REFERENCES.md).

## Read the article

[FinGuard: What Happens When a Financial AI Agent Ignores the Rules?](https://zabahana.github.io/FinGuard/) is the public article with all seven figures. For Medium, use **Stories → Import a story** with that URL, then review the imported images and captions. See [Pages publication maintenance](docs/GITHUB_PAGES.md).

## Two complementary studies

**Study 1: Control-Layer Ablation** tests 14 deterministic attacks and four positive controls across four configurations (72 outcomes). **Study 2: Model-Driven Adversarial Evaluation** measures model proposals and their enforcement outcomes; these counts are not pooled.

### Model-driven evaluation

The [expanded model-security study](docs/MODEL_EVALUATION.md) evaluates 200 adversarial continuations, 50 benign workflows, and 50 multi-turn episodes. It separates prohibited proposals, control blocking, unauthorized backend execution, false blocks, legitimate workflow completion, and recovery after a block. The saved benign traces show 34/50 completed workflows, 0/133 false blocks, and 1/17 recovery after a block (5.9%); security and reliability are separate measurements. The [versioned corpus](evaluation/model-security-corpus.json) and [recorded results](docs/visuals/model-evaluation-snapshot.json) accompany the implementation. These application-control tests run on the trusted host; OpenShell containment evidence remains a separate experiment.

## Current implementation

Explore the [interactive visual guide](docs/visual-guide.html), [Mermaid component and process diagrams](docs/ARCHITECTURE.md), and [Medium article draft](docs/MEDIUM_ARTICLE.md). The visual guide works offline and separates detector metrics, agent outcomes, and runtime verification. See [visual documentation maintenance](docs/VISUALS.md) to refresh its snapshot or export diagrams.

FinGuard includes a dependency-free synthetic banking simulation and a real-data fraud workflow using the ULB/Worldline credit-card dataset. A trained classifier scores held-out transactions, and a local Qwen agent investigates through guarded, label-blind tools. The original fictional bank, deterministic agent, 18 curated security scenarios, and optional synthetic FastAPI service remain available.

For the real dataset, training procedure and model-driven investigation commands, see [Real ULB transactions](docs/ULB.md).

```sh
.venv/bin/python -m finguard investigate-transaction
```

This command requires the dataset and trained detector described in that guide; both are already installed on the development Mac. Transaction data is real and anonymized; case submission remains simulated.

**The original Python simulation is not an OS security boundary.** Its virtual attack benchmarks cannot establish runtime containment or LLM resistance to prompt injection. A separate [OpenShell integration](docs/OPENSHELL.md) now runs the real-data agent inside NVIDIA OpenShell 0.1.2 on Docker Desktop, with actual filesystem/network probes and native OCSF audit evidence.

To use the verified OpenShell sandbox already running on this Mac:

```sh
sh scripts/investigate-openshell.sh
```

Direct `python -m finguard` commands still run outside OpenShell unless executed through that integration.

## Run locally

For an interactive operator workspace with real job execution, progress logs, detector charts, containment results, and Mermaid diagrams:

```sh
.venv/bin/python -m finguard.web
```

Open **http://127.0.0.1:8766**. See [web UI setup and workflow controls](docs/WEB_UI.md). The console runs trusted host commands; its investigation button invokes the OpenShell integration.

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

For a remote Linux instance, see [Run on NVIDIA Brev](docs/BREV.md). The setup script runs tests and all three virtual benchmark modes; it does not provision infrastructure.

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
- `docs/.github/workflows/test.yml`: GitHub Actions template. CI is not enabled yet; move this file to `.github/workflows/test.yml` at the repository root and push with a credential that has workflow permission to enable it.

## Attack Lab

The local web UI includes a runnable [Attack Lab](docs/ATTACK_LAB.md): bounded application-abuse and runtime fixtures across four control configurations, plus separate Qwen prompt-injection continuations. Inspect attempts, decisions, and native network evidence without conflating model compliance with runtime enforcement.

## Interpreting results

Attack deny rate counts only explicit denials. Attack prevention also counts review holds, because review does not execute an action. False block rate counts denied legitimate actions; legitimate review rate is reported separately. Completion requires every step of a legitimate scenario to execute. Exfiltration rate counts executed actions labeled as virtual sensitive-data sinks. Runtime policy violation rate uses independently labeled forbidden steps, not the policy's own decisions, as ground truth.

Decision latency measures the Python policy check only. OpenShell overhead and GPU utilization are `null` until real measurements are available. Reports separate `enforcement_failure`, `semantic_failure` and `held_for_review` outcomes. In unrestricted mode, an `enforcement_failure` label indicates a violated reference policy, not failure of an installed sandbox.

The semantic rules deliberately trade utility for caution. The profile fixture contains an SSN; subsequent outbound actions enter review even when their payload appears harmless. There is no reviewer approval interface yet. Direct SSN matching does not recognize every encoding, and history is only a coarse sensitivity signal. All chained steps are attempted independently; data dependencies are not dynamically propagated.

## Next milestones

1. Extend the verified local OpenShell integration to a production host with service-side banking authorization and durable audit delivery.
2. Extend the local Qwen tool-calling adapter with held-out model-driven attack evaluations.
3. Add PostgreSQL persistence, authenticated API sessions, and auditable human review.
4. Correlate OCSF telemetry, model traces and GPU measurements, then run held-out ablations.

No cloud resources are provisioned by this repository. All included identities, credentials and account data are fictional.

## Local model on macOS

FinGuard now supports a real tool-calling model through Ollama's loopback API.
The default is `qwen3:8b` (Q4_K_M, approximately 5.2 GB of weights), a practical
starting point for the 24 GB Apple Silicon development Mac. Inference uses
Ollama's Metal backend. This is pretrained inference, not model training.

On this checkout, Ollama and the model are installed under ignored `.local/`.
To restart the model server in a terminal:

```sh
sh scripts/serve-model.sh
```

In another terminal, run a real investigation:

```sh
.venv/bin/python -m finguard investigate --agent ollama --model qwen3:8b --output artifacts/local-model
```

For a fresh machine, install [Ollama](https://ollama.com/download/mac), start
its server with `OLLAMA_NO_CLOUD=1 ollama serve`, then `ollama pull qwen3:8b`.
The project-local server script is only for this checkout's `.local` installation.
Select another installed tool-capable, non-thinking-compatible local model using
`--model MODEL`. The adapter disables thinking and uses an 8192-token context.
No API key is needed. The client uses only `127.0.0.1:11434` and bypasses proxies.

The model chooses virtual file reads, transaction/risk queries and case submission.
Each valid action goes through the existing Runner and policy, with one session
per investigation. Argument validation rejects unknown tools and extra fields.
Completion requires successful evidence reads and an allowed case submission;
model prose alone cannot report success. `--max-steps` bounds inference turns
(default 12, maximum 50), each with at most eight calls and a 180-second timeout.
The process returns a nonzero status for failed or incomplete investigations.

Reports include the submitted recommendation, model name, inference wall time,
call counts and generated token count. Known sensitive identifiers are redacted
from saved recommendations; raw model conversations and tool results are not
persisted. This is not a general-purpose PII scrubber. Cases remain in memory.
The HTTP fixture service remains separate; use the CLI for model investigations.
The existing `evaluate` command still benchmarks deterministic virtual scenarios,
not LLM prompt-injection resistance. A completed case is a workflow result, not
an independent assessment of the model's reasoning quality or a real OS sandbox.
